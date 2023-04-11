# flake8: noqa

import os
import csv
import json
from datetime import datetime
import time

import requests

from models import (
    BASE_URL,
    REQUEST_HEADERS,
    Session,
    Bill,
    LegislatorProfile,
    Committee
)

TODAY = datetime.now().date().today().isoformat()


def gather_historical_legislator_data():

    filepath = os.path.abspath(
        os.path.join(
            os.path.dirname( __file__ ),
            '..',
            'data',
            'legislators',
            'sd-legislature-legislators-historical.json'
        )
    )

    r = requests.get(
        f'{BASE_URL}/api/Historical/AllFlatMembers',
        headers=REQUEST_HEADERS
    )

    data = r.json()
    data_out = []

    for leg in data:
        birthday = leg.get('Birthdate')
        deathday = leg.get('Deathdate')

        if birthday:
            try:
                birthday = datetime.strptime(birthday, '%m-%d-%Y').date().isoformat()
            except ValueError:
                pass
        if deathday:
            try:
                deathday = datetime.strptime(deathday, '%m-%d-%Y').date().isoformat()
            except ValueError:
                pass

        notes = leg.get('Remarks')

        if notes:
            notes = ' '.join(notes.split())


        d = {
            'legislator_id_canon': leg.get('MemberId'),
            'name_first': leg.get('FirstName'),
            'name_last': leg.get('LastName'),
            'name_middle': leg.get('MiddleName'),
            'gender': leg.get('Gender'),
            'birthday': birthday,
            'deathday': deathday,
            'member_type': leg.get('MemberType'),
            'counties': leg.get('County'),
            'cities': leg.get('City'),
            'year_start': leg.get('StartYear'),
            'year_end': leg.get('EndYear'),
            'notes': notes,
            'offices': leg.get('Office'),
            'parties': leg.get('Party'),
            'chambers': leg.get('Body')
        }

        data_out.append(d)

    with open(filepath, 'w') as outfile:
        outfile.write(json.dumps(data_out))

    print(f'Downloaded {filepath}')


def get_legislator_xwalk():

    filepath = os.path.abspath(
        os.path.join(
            os.path.dirname( __file__ ),
            'sd-legislator-xwalk.csv'
        )
    )

    with open(filepath, 'r') as infile:
        data = {x['legislator_profile_id']: x['legislator_id_canon'] for x in list(csv.DictReader(infile))}
    
    return data


def get_session_dates_lookup():
    filepath = os.path.abspath(
        os.path.join(
            os.path.dirname( __file__ ),
            'session-dates.json'
        )
    )

    with open(filepath, 'r') as infile:
        data = json.load(infile)

    return data


def gather_session_data():

    leg_xwalk = get_legislator_xwalk()
    session_dates = get_session_dates_lookup()

    sessions = requests.get(
        f'{BASE_URL}/api/Sessions',
        headers=REQUEST_HEADERS
    ).json()

    for sesh in sessions:
        sesh_id = sesh.get('SessionId')
        session = Session(
            session_id=sesh_id,
            lookup_table=session_dates
        )

        print(session)

        session.get_session_docs()
        time.sleep(0.5)

        session.get_bills()
        time.sleep(0.5)

        session.get_legislators()
        time.sleep(0.5)

        session.get_committees()
        time.sleep(0.5)

        session.get_session_laws()
        time.sleep(0.5)

        session.get_conference_committees()
        time.sleep(0.5)

        if not session.file_exists or session.is_current_session:
            session.write_local_file()

        session_laws = session.session_data.get('session_laws')

        # get Legislator data
        for leg_id in session.session_data.get('legislators'):
            profile = LegislatorProfile(
                session_id=sesh_id,
                legislator_profile_id=leg_id,
                lookup_table=leg_xwalk
            )

            print(profile)

            if not profile.file_exists:
                profile.get_profile_data()
                time.sleep(0.5)

                print(profile)

                profile.get_canonical_id()
                profile.write_local_file()

                time.sleep(0.5)

        # get bill data
        for bill_id in session.session_data.get('bills'):
            bill = Bill(session_id=sesh_id, bill_id=bill_id)
            print(bill)

            if not bill.file_exists or session.is_current_session:
                bill.get_bill_data()
                time.sleep(0.5)

                bill.get_audio_data()
                time.sleep(0.5)

                bill.get_bill_versions()
                time.sleep(0.5)

                bill.get_amendments()
                time.sleep(0.5)

                bill.get_fiscal_notes()
                time.sleep(0.5)

                bill.get_action_log()
                time.sleep(0.5)

                if session_laws.get(bill_id):
                    bill.bill_data['session_law'] = session_laws.get(bill_id)

                bill.write_local_file()

        # get committee data
        for committee_id in session.session_data.get('committees'):
            committee = Committee(
                session_id=sesh_id,
                committee_id=committee_id
            )

            print(committee)

            if not committee.file_exists or session.is_current_session:
                committee.get_committee_data()
                committee.write_local_file()

        time.sleep(0.5)



if __name__ == '__main__':

    objects = [
        'sessions',
        'lobbyists',
        'legislators',
        'bills',
        'committees'
    ]

    for obj in objects:

        data_path = os.path.abspath(
            os.path.join(
                os.path.dirname( __file__ ),
                '..',
                'data',
                obj
            )
        )

        if not os.path.exists(data_path):
            os.makedirs(data_path)

    gather_historical_legislator_data()
    gather_session_data()
