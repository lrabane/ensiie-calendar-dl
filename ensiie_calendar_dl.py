#!/usr/bin/python

import sys, requests, bs4, re, json, icalendar, datetime, time

def main():
    if not 4 <= len(sys.argv) <= 5:
        exit('Wrong arguments, expected: username password output.ics [loop]')

    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.112 Safari/535.1',
                            'Accept': 'text/html',
                            'Accept-Encoding': 'gzip, deflate, br',
                            'Accept-Language': 'fr-FR,fr;q=0.5',
                            'Sec-Fetch-Mode': 'navigate',
                            'Sec-Fetch-User': '?1',
                            'Sec-Fetch-Site': 'same-origin',
                            'Connection': 'keep-alive',
                            'Upgrade-Insecure-Requests': '1',
                            'Cache-Control': 'max-age=0',
                            'DNT': '1'})

    result = ConnectToAurion(session, sys.argv[1], sys.argv[2])

    calendar_data = GetCalendarData(session, result)
    calendar_json = ParseJsonBody(calendar_data)
    calendar = generate_calendar(calendar_json)
    write_calendar(calendar, sys.argv[3])

def ConnectToAurion(session, username, password):
    result = session.get('https://aurionweb.ensiie.fr/', verify=False)
    execution = ParseExecution(result.text)
    
    session.headers.update({'Referer': 'https://cas.ensiie.fr/login?service=https%3A%2F%2Faurionweb.ensiie.fr%2F%2Flogin%2Fcas',
                            'Origin': 'https://cas.ensiie.fr'})

    payload = {'username': username,
               'password': password,
               'execution': execution,
               '_eventId': 'submit',
               'geolocation': '',
               'submit': 'LOGIN'}

    return session.post(result.url, data=payload)

def GetCalendarData(session, result):
    session.headers.update({'Referer': 'https://aurionweb.ensiie.fr/',
                            'Origin': 'https://aurionweb.ensiie.fr'})
    
    viewState = ParseViewState(result.text)
    mainMenuForm = ParseMainMenuForm(result.text)
    calendarMenuId = ParseCalendarMenuId(result.text)

    payload = {'javax.faces.partial.ajax': 'true',
               'javax.faces.source': mainMenuForm,
               'javax.faces.partial.execute': mainMenuForm,
               'javax.faces.partial.render': 'form:sidebar',
               mainMenuForm: mainMenuForm,
               'webscolaapp.Sidebar.ID_SUBMENU': calendarMenuId,
               'form': 'form',
               'form:largeurDivCenter': '1603',
               'form:sauvegarde': '',
               'javax.faces.ViewState': viewState}

    result = session.post('https://aurionweb.ensiie.fr/faces/MainMenuPage.xhtml', data=payload)

    calendarSubMenuId = ParseCalendarSubMenuId(result.text)

    payload = {'form': 'form',
               'form:largeurDivCenter': '1603',
               'form:sauvegarde': '',
               'javax.faces.ViewState': viewState,
               'form:sidebar': 'form:sidebar',
               'form:sidebar_menuid': calendarSubMenuId}


    result = session.post('https://aurionweb.ensiie.fr/faces/MainMenuPage.xhtml', data=payload)

    viewState = ParseViewState(result.text)
    calendarForm = ParseCalendarForm(result.text)

    payload = {'javax.faces.partial.ajax': 'true',
               'javax.faces.source': calendarForm,
               'javax.faces.partial.execute': calendarForm,
               'javax.faces.partial.render': calendarForm,
               calendarForm: calendarForm,
               '{}_start'.format(calendarForm): '0',
               '{}_end'.format(calendarForm): '3155760000000',
               'form': 'form',
               'form:largeurDivCenter': '01/01/2020',
               'form:week': '01-2020',
               '{}_view'.format(calendarForm): 'agendaWeek',
               'form:offsetFuseauNavigateur': '0',
               'form:onglets_activeIndex': '0',
               'form:onglets_scrollState': '0',
               'javax.faces.ViewState': viewState}

    return session.post('https://aurionweb.ensiie.fr/faces/Planning.xhtml', data=payload).text

def ParseExecution(body):
    soup = bs4.BeautifulSoup(body, 'html.parser')
    return soup.find(attrs={'name': 'execution'})['value']

def ParseViewState(body):
    soup = bs4.BeautifulSoup(body, 'html.parser')
    return soup.find('input', id='j_id1:javax.faces.ViewState:0')['value']

def ParseMainMenuForm(body):
    return re.search('chargerSousMenu = function\(\) {PrimeFaces.ab\({s:"(form:j_idt\d+?)",f:"form"', body).group(1)

def ParseCalendarMenuId(body):
    return re.search('<li class="ui-widget ui-menuitem ui-corner-all ui-menu-parent (submenu_\d+?)" role="menuitem" aria-haspopup="true"><a href="#" class="ui-menuitem-link ui-submenu-link ui-corner-all" tabindex="-1"><span class="ui-menuitem-text">Emploi du temps<\/span>', body).group(1)

def ParseCalendarSubMenuId(body):
    return re.search('PrimeFaces\.addSubmitParam\(\'form\',{\'form:sidebar\':\'form:sidebar\',\'form:sidebar_menuid\':\'(\d_\d)\'}\)\.submit\(\'form\'\);return false;"><span class="ui-menuitem-text">Mon planning \(apprenant\)<\/span>', body).group(1)
    
def ParseCalendarForm(body):
    soup = bs4.BeautifulSoup(body, 'html.parser')
    return soup.find(attrs={'class': 'schedule'}).get('id')

def ParseJsonBody(body):
    return json.loads(re.search('<!\[CDATA\[\{"events" : (.+?)\}]]>', body).group(1))

def generate_calendar(json):
    calendar = icalendar.Calendar()
    calendar['summary'] = 'Planning ENSIIE'
    
    for evt in json:
        event = icalendar.Event()
        event.add('summary', evt['title'])
        event.add('dtstart', datetime.datetime.strptime(evt['start'], '%Y-%m-%dT%H:%M:%S%z'))
        event.add('dtend', datetime.datetime.strptime(evt['end'], '%Y-%m-%dT%H:%M:%S%z'))
        calendar.add_component(event)

    return calendar

def write_calendar(calendar, output_path):
    with open(output_path, 'wb') as output:
        output.write(calendar.to_ical())

if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[4] == "loop":
        while True:
            main()
            now = datetime.datetime.now()
            tomorrow = now.replace(hour=4, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
            delta = tomorrow - now
            print(f"sleeping for {delta} until {tomorrow}")
            time.sleep(delta.seconds)
    else:
        main()
