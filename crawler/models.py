# flake8: noqa

import os
import json
import time

import requests
from bs4 import BeautifulSoup


BASE_URL = 'https://sdlegislature.gov'
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'

REQUEST_HEADERS = {
    'User-Agent': USER_AGENT
}


class Session(object):
    ''' A session of the S.D. Legislature '''

    def __init__(
        self,
        session_id,
        lookup_table={},
        historical_legislator_data=None
    ):
        self.session_id = session_id
        self.lookup_table = lookup_table
        self.historical_legislator_data = historical_legislator_data

        self.api_route = f'{BASE_URL}/api/Sessions/{self.session_id}'

        self.local_file = os.path.abspath(
            os.path.join(
                os.path.dirname( __file__ ),
                '..',
                'data',
                'sessions',
                f'sd-legislature-session-{self.session_id}.json'
            )
        )

        self.file_exists = os.path.exists(self.local_file)

        self.get_session_data()

        self.name = self.session_data.get('session_name')
        self.is_current_session = self.session_data.get('is_current_session')


    def get_session_data(self):
        ''' Get basic data on this session '''

        r = requests.get(
            self.api_route,
            headers=REQUEST_HEADERS
        )

        r.raise_for_status()

        data = r.json()

        session_id = str(data.get('SessionId'))
        start_date = self.lookup_table.get(session_id).get('start_date')
        end_date = self.lookup_table.get(session_id).get('end_date')

        session_data = {
            'session_id': session_id,
            'session_name': data.get('YearString'),
            'session_number': data.get('SessionNumber'),
            'is_current_session': data.get('CurrentSession'),
            'is_special_session': data.get('SpecialSession'),
            'start_date': start_date,
            'end_date': end_date
        }

        self.session_data = session_data

        return self

    def get_session_docs(self):
        ''' Get documents attached to this session '''

        # grab document details for this session
        docs_url = f'{BASE_URL}/api/Documents/DocumentType?'

        # can't use params dict because of repeating key names
        doctypes = [24, 68, 60, 71, 72, 73, 74]
        querystring = f'SessionIds={self.session_id}&{"&".join([f"Type={x}" for x in doctypes])}'

        r = requests.get(
            f'{docs_url}{querystring}',
            headers=REQUEST_HEADERS
        )
        r.raise_for_status()

        data = r.json()
        data_out = []

        for doc in data:

            file_ext = doc.get('WebFilename').split('.')[-1]
            doc_id = doc.get('DocumentId')
            url = f'https://mylrc.sdlegislature.gov/api/Documents/{doc_id}.{file_ext}'

            d = {
                'session_id': doc.get('SessionId'),
                'document_id': doc.get('DocumentId'),
                'document_title': doc.get('Title'),
                'document_date': doc.get('DocumentDate'),
                'document_type': doc.get('DocumentType'),
                'document_url': url
            }

            data_out.append(d)

        self.session_data['docs'] = data_out

        return self

    def get_bills(self):
        ''' Get a list of IDs of bills in this session '''

        r = requests.get(
            f'{BASE_URL}/api/Bills/Session/Light/{self.session_id}',
            headers=REQUEST_HEADERS
        )

        r.raise_for_status()

        self.session_data['bills'] = [x.get('BillId') for x in r.json()]

        return self

    def get_legislators(self):
        ''' Get IDs of legislator profiles for this session '''

        r = requests.get(
            f'{BASE_URL}/api/SessionMembers/Session/{self.session_id}',
            headers=REQUEST_HEADERS
        )

        r.raise_for_status()

        self.session_data['legislators'] = [x.get('SessionMemberId') for x in r.json()]

        return self

    def get_committees(self):
        ''' Get IDs of committees for this session '''

        r = requests.get(
            f'{BASE_URL}/api/SessionCommittees/Session/{self.session_id}',
            headers=REQUEST_HEADERS
        )

        r.raise_for_status()

        self.session_data['committees'] = [x.get('SessionCommitteeId') for x in r.json()]

        return self

    def get_conference_committees(self):
        ''' Get details on conference committees for this session '''

        r = requests.get(
            f'{BASE_URL}/api/ConferenceCommittees/Session/{self.session_id}',
            headers=REQUEST_HEADERS
        )

        r.raise_for_status()

        data = r.json()
        data_out = []

        if data:
            for cmt in data:
                committee = cmt[0]

                report = committee.get('Report')

                if report:
                    report = f"https://mylrc.sdlegislature.gov/api/Documents/{report.get('DocumentId')}.pdf"

                minutes = committee.get('Minutes')

                if minutes:
                    minutes = f"https://mylrc.sdlegislature.gov/api/Documents/{minutes.get('DocumentId')}.pdf"
                
                d = {
                    'meeting_time': committee.get('MeetingTime'),
                    'bill_id': committee.get('Bill').get('BillId'),
                    'staff': committee.get('Staff'),
                    'secretary': committee.get('Secretary'),
                    'minutes': minutes,
                    'report': report
                }

                data_out.append(d)

        self.session_data['conference_committees'] = data_out

        return self

    def get_session_laws(self):
        ''' Map bill IDs to session laws passed during this session '''

        r = requests.get(
            f'{BASE_URL}/api/SessionLaws/{self.session_id}',
            headers=REQUEST_HEADERS
        )

        r.raise_for_status()
        data = r.json()
        data_out = {}

        for sd in data:
            data_out[sd.get('BillId')] = sd.get('SessionLawId')

        self.session_data['session_laws'] = data_out

        return self

    def write_local_file(self):
        ''' Write session data to file '''

        with open(self.local_file, 'w') as outfile:
            json.dump(self.session_data, outfile)

        print(f'Downloaded {self.local_file}')

    def __str__(self):
        return f'{self.name} session - South Dakota Legislature ({self.session_id})'


class Bill(object):
    ''' A bill introduced during a particular Session '''

    def __init__(self, session_id=None, bill_id=None):
        self.bill_id = bill_id
        self.session_id = session_id
        self.api_route = f'{BASE_URL}/api/Bills/{self.bill_id}'

        self.local_file = os.path.abspath(
            os.path.join(
                os.path.dirname( __file__ ),
                '..',
                'data',
                'bills',
                f'sd-legislature-bill-{self.bill_id}.json'
            )
        )

        self.file_exists = os.path.exists(self.local_file)


    def get_bill_data(self):
        ''' Get basic details on this bill '''

        r = requests.get(
            self.api_route,
            headers=REQUEST_HEADERS
        )

        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            self.bill_data = {}
            return self

        data = r.json()

        sponsors = []

        for sponsor in data.get('BillSponsor'):
            is_prime = False

            if sponsor.get('SponsorType') == 'P':
                is_prime = True

            sponsors.append({
                'legislator_profile_id': sponsor.get('SessionMemberId'),
                'is_prime': is_prime
            })

        bill_title = data.get('Title')

        self.bill_data = {
            'session_id': self.session_id,
            'bill_id': data.get('BillId'),
            'bill_type': data.get('BillTypeFull'),
            'bill_number': data.get('BillNumber'),
            'bill_title': bill_title,
            'sponsors': sponsors,
            'keywords': [x.get('Keyword') for x in data.get('Keywords')]
        }

        return self


    def get_audio_data(self):
        ''' Get details on audio of hearings about this bill '''

        url = f'{BASE_URL}/api/Bills/Audio/{self.bill_id}'

        r = requests.get(
            url,
            headers=REQUEST_HEADERS
        )

        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            self.bill_data['audio'] = []
            return self

        data = r.json()
        data_out = []

        for audio in data:
            data_out.append({
                'meeting_datetime': audio.get('MeetingDate'),
                'committee': audio.get('CommitteeCode'),
                'url': audio.get('Url'),
                'start_seconds': audio.get('StartSeconds')
            })

        self.bill_data['audio'] = data_out

        return self

    def get_bill_versions(self):

        ''' Gather details on each version of the bill considered '''
        def parse_bill_html(html):

            soup = BeautifulSoup(html, 'html.parser')

            # new style
            div = soup.find('div', {'title': 'header'})

            if div:
                # nuke the header and footer and "unsupported" divs
                div.extract()
                footer = soup.find('div', {'title': 'footer'})

                if footer:
                    footer.extract()
                unsupported = soup.find('div', {'id': 'unsupported'})

                if unsupported:
                    unsupported.extract()
                grafs = [x.text.strip() for x in soup.find_all('p')]
                bill_text_raw = ' '.join(grafs)
            else:
                # old style
                try:
                    div = soup.find_all('table')[0].parent
                    for table in div.find_all('table'):
                        table.extract()
                    bill_text_raw = ' '.join([x.text.strip() for x in div.find_all('div')])
                except IndexError:
                    return ''

            return ' '.join(bill_text_raw.split())

        r = requests.get(
            f'{BASE_URL}/api/Bills/Versions/{self.bill_id}',
            headers=REQUEST_HEADERS
        )

        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            self.bill_data['bill_versions'] = []
            return self

        data = r.json()
        data_out = []

        for version in data:
            bill_version_id = version.get('DocumentId')

            d = {
                'bill_id': self.bill_id,
                'bill_version_id': bill_version_id,
                'bill_version': version.get('BillVersion'),
                'bill_version_date': version.get('DocumentDate')
            }

            r = requests.get(
                f'{BASE_URL}/api/Bills/HTML/{bill_version_id}',
                headers=REQUEST_HEADERS
            )

            data = r.json()

            try:
                parsed_text = parse_bill_html(data.get('DocumentHtml'))
            except TypeError:
                parsed_text = ''

            d['bill_text'] = parsed_text

            data_out.append(d)


        self.bill_data['bill_versions'] = data_out

        return self


    def get_amendments(self):
        ''' Get details on amendments offered to this bill '''

        r = requests.get(
            f'{BASE_URL}/api/Bills/Amendments/{self.bill_id}',
            headers=REQUEST_HEADERS
        )

        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            self.bill_data['amendments'] = []
            return self

        data = r.json()
        data_out = []

        for amd in data:
            doc_id = amd.get('DocumentId')
            doc_id_instructions = amd.get('AmendmentInstructionsDocumentId')

            d = {
                'bill_id': self.bill_id,
                'document_id': amd.get('DocumentId'),
                'document_url': f'https://mylrc.sdlegislature.gov/api/Documents/{doc_id}.pdf',
                'legislator_profile_id': amd.get('SessionMemberId'),
                'document_id_instructions': doc_id_instructions,
                'document_id_instructions_url': f'https://mylrc.sdlegislature.gov/api/Documents/{doc_id_instructions}.pdf',
            }

            data_out.append(d)

        self.bill_data['amendments'] = data_out

        return self


    def get_fiscal_notes(self):
        ''' Get document IDs of fiscal notes for this bill '''

        r = requests.get(
            f'{BASE_URL}/api/Bills/FiscalNotes/{self.bill_id}',
            headers=REQUEST_HEADERS
        )

        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            self.bill_data['fiscal_notes'] = []
            return self

        data = r.json()

        self.bill_data['fiscal_notes'] = [x.get('DocumentId') for x in data]

        return self


    def get_action_log(self):
        ''' Get details, including votes, on actions taken on this bill '''

        r = requests.get(
            f'{BASE_URL}/api/Bills/ActionLog/{self.bill_id}',
            headers=REQUEST_HEADERS
        )

        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            self.bill_data['action_log'] = []
            return self

        data = r.json()
        data_out = []

        for item in data:
            vote = item.get('Vote')
            vote_data = {}

            if vote:
                vote_id = vote.get('VoteId')
                vote_data['vote_id'] = vote_id
                vote_data['president_vote'] = vote.get('PresidentVote')

                r = requests.get(
                    f'{BASE_URL}/api/Votes/{vote_id}',
                    headers=REQUEST_HEADERS
                )

                r.raise_for_status()

                data = r.json()

                for rc in data.get('RollCalls'):
                    key = rc.get('Vote1')

                    if not vote_data.get(key):
                        vote_data[key] = []

                    vote_data[key].append(rc.get('SessionMemberId'))

                time.sleep(0.5)

            committee_id_assigned = item.get('AssignedCommittee')

            if committee_id_assigned:
                committee_id_assigned = committee_id_assigned.get('AssignedCommitteeId')

            committee_id_action = item.get('ActionCommittee')

            if committee_id_action:
                committee_id_action = committee_id_action.get('ActionCommitteeId')

            doc_id = item.get('DocumentId')

            d = {
                'bill_id': self.bill_id,
                'action_date': item.get('ActionDate'),
                'document_id': doc_id,
                'document_url': f'https://mylrc.sdlegislature.gov/api/Documents/{doc_id}.pdf',
                'status_text': item.get('StatusText'),
                'journal_page': item.get('JournalPage'),
                'committee_id_action': committee_id_action,
                'committee_id_assigned': committee_id_assigned,
                'result': item.get('Result'),
                'vote': vote_data
            }

            data_out.append(d)

        self.bill_data['action_log'] = data_out

        return self


    def write_local_file(self):
        ''' Write data to file '''

        with open(self.local_file, 'w') as outfile:
            json.dump(self.bill_data, outfile)

        print(f'Downloaded {self.local_file}')


    def __str__(self):
        return f'Bill ID #{self.bill_id} - South Dakota Legislature session {self.session_id}'


class LegislatorProfile(object):
    ''' A Legislator serving in a particular Session '''

    def __init__(
        self,
        session_id=None,
        legislator_profile_id=None,
        lookup_table={},
        historical_legislator_data=None
    ):
        self.session_id = session_id
        self.historical_legislator_data = historical_legislator_data

        # lookup table to map session profile IDs to canonical historical IDs
        self.lookup_table = lookup_table
        self.legislator_profile_id = legislator_profile_id
        self.api_route = f'{BASE_URL}/api/SessionMembers/Detail/{self.legislator_profile_id}'

        self.local_file = os.path.abspath(
            os.path.join(
                os.path.dirname( __file__ ),
                '..',
                'data',
                'legislators',
                f'sd-legislature-legislator-{self.legislator_profile_id}.json'
            )
        )

        self.file_exists = os.path.exists(self.local_file)


    def get_profile_data(self):
        ''' Get basic details about this legislator during this session '''

        r = requests.get(
            self.api_route,
            headers=REQUEST_HEADERS
        )

        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            self.profile_data = {}
            return self

        data = r.json()

        self.profile_data = {
            'session_id': self.session_id,
            'year': data.get('Year'),
            'legislator_profile_id': data.get('SessionMemberId'),
            'chamber': data.get('MemberType'),
            'name': data.get('FirstLastName'),
            'district': data.get('District'),
            'address1': data.get('HomeAddress1'),
            'address2': data.get('HomeAddress2'),
            'city': data.get('HomeCity'),
            'state': data.get('HomeState'),
            'zipcode': data.get('HomeZip'),
            'phone_home': data.get('HomePhone'),
            'phone_capitol': data.get('CapitolPhone'),
            'phone_biz': data.get('BusinessPhone'),
            'phone_cell': data.get('CellPhone'),
            'email': data.get('EmailState'),
            'picture': data.get('Picture'),
            'party': data.get('PartyName'),
            'term': data.get('MemberTermName'),
            'occupation': data.get('Occupation'),
            'counties': data.get('Counties')
        }

        self.name = self.profile_data.get('name')


    def get_canonical_id(self):
        ''' Look up this profile's canonical ID '''

        profile_id = str(self.legislator_profile_id)
        canon_id = self.lookup_table.get(profile_id)

        if not canon_id:
            print(f'Need to map legislator profile to canonical member ID: {self.name} - {profile_id}')

            profile_bits = '\n'.join([
                f'    - {self.profile_data.get("chamber", "")}',
                f'    - {self.profile_data.get("party", "")}',
                f'    - {self.profile_data.get("city", "")}',
                f'    - {self.profile_data.get("counties", "")}'
            ])

            print(profile_bits)

            matches = [x for x in self.historical_legislator_data if x.get('name_last', '').upper() in self.name.upper() and x.get('name_first', '').upper() in self.name.upper()]

            if matches:
                print('\nPossible matches:')
                for match in matches:
                    canon_bits = '\n'.join([
                        f'    - {match.get("name_first", "")} {match.get("name_last", "")} ({match.get("year_start", "")}-{match.get("year_end", "")}) - {match.get("legislator_id_canon", "")}',
                        f'    - {match.get("chambers", "")}',
                        f'    - {match.get("parties", "")}',
                        f'    - {match.get("cities", "")}',
                        f'    - {match.get("counties", "")}'
                    ])

                    print(canon_bits)
                    print()

        try:
            canon_id = int(canon_id)
        except ValueError:
            print(canon_id)
            pass

        self.profile_data['legislator_canonical_id'] = canon_id

        return self


    def write_local_file(self):
        ''' Write data to file '''

        with open(self.local_file, 'w') as outfile:
            json.dump(self.profile_data, outfile)

        print(f'Downloaded {self.local_file}')

    def __str__(self):
        return f'South Dakota Legislator ID #{self.legislator_profile_id}, session ID #{self.session_id}'


class Committee(object):
    ''' A Committee that meets during a Session '''

    def __init__(self, session_id=None, committee_id=None):
        self.session_id = session_id
        self.committee_id = committee_id
        self.api_route = f'{BASE_URL}/api/SessionCommittees/Detail/{self.committee_id}'

        self.local_file = os.path.abspath(
            os.path.join(
                os.path.dirname( __file__ ),
                '..',
                'data',
                'committees',
                f'sd-legislature-committee-{self.committee_id}.json'
            )
        )

        self.file_exists = os.path.exists(self.local_file)


    def get_committee_data(self):
        ''' Get basic details on this committee '''

        r = requests.get(
            self.api_route,
            headers=REQUEST_HEADERS
        )

        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            self.committee_data = {}
            return self

        data = r.json()

        self.committee_data = {
            'session_id': self.session_id,
            'committee_id': self.committee_id,
            'committee_name': data.get('Committee').get('FullName'),
            'committee_room': data.get('Committee').get('Room'),
            'committee_days': data.get('Committee').get('Days'),
            'is_full_body': data.get('FullBody'),
            'committee_id_canon': data.get('CommitteeId'),
            'chamber': data.get('Body'),
            'authority': data.get('Authority'),
            'members': [],
            'non_committee_members': data.get('NonCommitteeMembers'),
            'staff': [x.get('UserId') for x in data.get('Staff')]
        }

        for member in data.get('CommitteeMembers'):
            self.committee_data['members'].append({
                'legislator_profile_id': member.get('SessionMemberId'),
                'committee_member_type': member.get('CommitteeMemberType')
            })

        return self


    def write_local_file(self):
        ''' Write data to file '''

        with open(self.local_file, 'w') as outfile:
            json.dump(self.committee_data, outfile)

        print(f'Downloaded {self.local_file}')

    def __str__(self):
        return f'South Dakota Committee ID #{self.committee_id}, session ID #{self.session_id}'
