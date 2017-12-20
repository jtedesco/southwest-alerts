import arrow
import logging
import requests
import sys

from southwest import Southwest
import settings

DATETIME_FORMAT = 'YYYY-MM-DDTHH:mm'
DATE_FORMAT = 'YYYY-MM-DD'


def check_for_price_drops(username, password, email):
    southwest = Southwest(username, password)
    flights = [f for t in southwest.get_upcoming_trips()['trips'] for f in t['flights']]
    messages = []

    for flight in flights:
        try:
            if flight['internationalFlight']:
                logging.info('Skipping international flight')  # TODO use the desktop API to handle international flights
                continue

            first_name = flight['passengers'][0]['firstName']
            last_name = flight['passengers'][0]['lastName']
            record_locator = flight['recordLocator']
            cancellation_details = southwest.get_cancellation_details(record_locator, first_name, last_name)
            itinerary_price = cancellation_details['pointsRefund']['amountPoints']

            # Calculate total for all of the legs of the flight
            matching_flights_price = 0
            for origination_destination in cancellation_details['itinerary']['originationDestinations']:
                departure_datetime = arrow.get(origination_destination['segments'][0]['departureDateTime'])
                arrival_datetime = arrow.get(origination_destination['segments'][-1]['arrivalDateTime'])

                origin_airport = origination_destination['segments'][0]['originationAirportCode']
                destination_airport = origination_destination['segments'][-1]['destinationAirportCode']
                available = southwest.get_available_flights(
                    departure_datetime.format(DATE_FORMAT),
                    origin_airport,
                    destination_airport
                )

                # Find that the flight that matches the purchased flight
                matching_flight = next(f for f in available['trips'][0]['airProducts'] if f['segments'][0]['departureDateTime'] == departure_datetime.format(DATETIME_FORMAT) and f['segments'][-1]['arrivalDateTime'] == arrival_datetime.format(DATETIME_FORMAT))

                matching_flight_price = matching_flight['fareProducts'][-1]['pointsPrice']['discountedRedemptionPoints']
                matching_flight_price = min([f['pointsPrice']['discountedRedemptionPoints'] for f in matching_flight['fareProducts'] if f['pointsPrice']['discountedRedemptionPoints'] > 0])
                matching_flights_price += matching_flight_price

            # Calculate refund details (current flight price - sum(current price of all legs), and print log message
            refund_amount = itinerary_price - matching_flights_price
            message = '{base_message} points detected for flight {record_locator} from {origin_airport} to {destination_airport} on {departure_date}'.format(
                base_message='Price drop of {}'.format(refund_amount) if refund_amount > 0 else 'Price increase of {}'.format(refund_amount * -1),
                refund_amount=refund_amount,
                record_locator=record_locator,
                origin_airport=origin_airport,
                destination_airport=destination_airport,
                departure_date=departure_datetime.format(DATE_FORMAT)
            )
            logging.info(message)

            if refund_amount > 100:
                messages.append(message)
                logging.info('Sending email for price drop')
        except:
            logging.exception('error')

    if messages:
        resp = requests.post(
            'https://api.mailgun.net/v3/{}/messages'.format(settings.mailgun_domain),
            auth=('api', settings.mailgun_api_key),
            data={'from': 'Southwest Alerts <southwest-alerts@{}>'.format(settings.mailgun_domain),
                  'to': [email],
                  'subject': 'Southwest Price Drop Alert',
                  'text': '\n'.join(messages)})


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='[%(asctime)s] %(levelname)s:\t%(message)s')
    for user in settings.users:
        check_for_price_drops(user.username, user.password, user.email)
