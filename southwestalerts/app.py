import arrow
import logging
import requests
import settings
import southwest
import sys


DATETIME_FORMAT = 'YYYY-MM-DDTHH:mm'
DATE_FORMAT = 'YYYY-MM-DD'


def check_for_price_drops(username, password, email):
    southwest_session = southwest.Southwest(username, password)
    flights = [f for t in southwest_session.get_upcoming_trips()['trips'] for f in t['flights']]
    messages = []

    for flight in flights:
        try:
            if flight['internationalFlight']:
                # TODO use the desktop API to handle international flights
                logging.info('Skipping international flight')
                continue

            first_name = flight['passengers'][0]['firstName']
            last_name = flight['passengers'][0]['lastName']
            record_locator = flight['recordLocator']
            cancellation_details = southwest_session.get_cancellation_details(
                    record_locator, first_name, last_name)
            if 'pointsRefund' not in cancellation_details:
                destinations = cancellation_details['itinerary']['originationDestinations']
                all_companion_fares = all(d['fareType'] == 'Companion' for d in destinations)
                if all_companion_fares:
                    logging.info('Skipping flight from {} to {} on {}, booked as companion.'.format(
                        destinations[0]['segments'][0]['originationAirportCode'],
                        destinations[0]['segments'][-1]['destinationAirportCode'],
                        arrow.get(destinations[0]['segments'][0]['departureDateTime']).format(DATE_FORMAT)))
                    continue

            itinerary_price = cancellation_details['pointsRefund']['amountPoints']

            # Calculate total for all of the legs of the flight
            matching_flights_price = 0
            for origination_destination in cancellation_details['itinerary']['originationDestinations']:
                departure_datetime = arrow.get(origination_destination['segments'][0]['departureDateTime'])
                arrival_datetime = arrow.get(origination_destination['segments'][-1]['arrivalDateTime'])

                origin_airport = origination_destination['segments'][0]['originationAirportCode']
                destination_airport = origination_destination['segments'][-1]['destinationAirportCode']
                available = southwest_session.get_available_flights(
                    departure_datetime.format(DATE_FORMAT),
                    origin_airport,
                    destination_airport
                )

                # Find that the flight that matches the purchased flight
                matching_flight = next(
                        f for f in available['trips'][0]['airProducts']
                        if (f['segments'][0]['departureDateTime'] == departure_datetime.format(DATETIME_FORMAT)
                            and f['segments'][-1]['arrivalDateTime'] == arrival_datetime.format(DATETIME_FORMAT)))

                matching_flight_price = (
                        matching_flight['fareProducts'][-1]['pointsPrice']['discountedRedemptionPoints'])
                matching_flight_price = min([
                    f['pointsPrice']['discountedRedemptionPoints']
                    for f in matching_flight['fareProducts']
                    if f['pointsPrice']['discountedRedemptionPoints'] > 0])
                matching_flights_price += matching_flight_price

            # Calculate refund details (current flight price - sum(current price of all legs), and print log message
            refund_amount = itinerary_price - matching_flights_price
            base_message = (
                    'Price drop of {}'.format(refund_amount)
                    if refund_amount > 0 else 'Price increase of {}'.format(refund_amount * -1))
            message_tpl = (
                    '{base_message} points detected for flight {record_locator} '
                    'from {origin_airport} to {destination_airport} on {departure_date}')
            message = message_tpl.format(
                base_message=base_message,
                refund_amount=refund_amount,
                record_locator=record_locator,
                origin_airport=origin_airport,
                destination_airport=destination_airport,
                departure_date=departure_datetime.format(DATE_FORMAT))
            logging.info(message)

            if refund_amount > 100:
                messages.append(message)
                logging.info('Sending email for price drop')
        except:
            logging.exception('error')

    if messages:
        send_email(email, '\n'.join(messages))


def send_email(email, message):
    resp = requests.post(
        'https://api.mailgun.net/v3/{}/messages'.format(settings.mailgun_domain),
        auth=('api', settings.mailgun_api_key),
        data={'from': 'Southwest Alerts <southwest-alerts@{}>'.format(settings.mailgun_domain),
              'to': [email],
              'subject': 'Southwest Price Drop Alert',
              'text': message})

    logging.info(resp)


if __name__ == '__main__':
    logging.basicConfig(
            stream=sys.stdout,
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s:\t%(message)s')
    for user in settings.users:
        check_for_price_drops(user.username, user.password, user.email)
