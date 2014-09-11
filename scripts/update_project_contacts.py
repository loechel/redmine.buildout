#!/usr/local/Plone/Python-2.7/bin/python
# -*- coding: utf-8 -*-

import sys
sys.path[0:0] = [
    '/usr/local/Plone/redmine.buildout/src/python-redmine',
    '/usr/local/Plone/redmine.buildout/src/python-redminecrm',
    '/usr/local/Plone/buildout-cache/eggs/ipython-1.2.1-py2.7.egg',
    '/usr/local/Plone/buildout-cache/eggs/ipdb-0.8-py2.7.egg',
    '/usr/local/Plone/buildout-cache/eggs/requests-2.3.0-py2.7.egg',
    ]

from redmine import Redmine
from redmine.exceptions import ResourceNotFoundError
from redmine.exceptions import ValidationError

import csv
import datetime
import os.path


def connect_projects_with_user(file_path):
    print file_path

    #redmine = Redmine('https://www.scm.verwaltung.uni-muenchen.de/internetdienste/', username='admin', password='admin')
    redmine = Redmine('http://localhost/internetdienste/', username='admin', password='admin')

    custom_fields = redmine.custom_field.all()
    cf_campus_kennung_id = None
    cf_fiona_gruppe_id = None
    cf_anrede_id = None
    cf_activ_id = None
    cf_inactiv_id = None

    for cf in custom_fields:
        if cf.name == "Campus-Kennung":
            cf_campus_kennung_id = cf.id
        elif cf.name == "Status":
            cf_status_id = cf.id
        elif cf.name == "Anrede":
            cf_anrede_id = cf.id
        elif cf.name == "Fiona aktiviert":
            cf_activ_id = cf.id
        elif cf.name == "Fiona deaktiviert":
            cf_inactiv_id = cf.id
        elif cf.name == "Fionagruppen":
            cf_fiona_gruppe_id = cf.id

    _all_contacts = redmine.contact.all()
    all_contacts = {}
    for contact in _all_contacts:
        fields = contact.custom_fields
        ck = 'keine_'+contact.last_name.lower()
        for field in fields:
            if field.name == 'Campus-Kennung':
                ck = field.value.strip().lower()
        print "add {user} to all_contacts".format(user=ck)
        all_contacts[ck] = contact

    with open(file_path, 'rb') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';', quotechar='"')

        error_store = {}

        #Fiona-Name;Fiona-Pfad;Playland-Titel;Erstellungsdatum;Status;URL;Sprache;Fionagruppe;

        project = 0
        for row in reader:
            #import ipdb; ipdb.set_trace()
            fiona_id = row.get('Fiona-Name')
            user_data = row.get('Fionagruppe')

            print "update Project: " + fiona_id

            if user_data != None:
                try:
                    project = redmine.project.get(fiona_id)
                    content = """
h1. Fionagruppen


"""



                    groups = user_data.split('#')

                    for group in groups:
                        if group != '':
                            group_data = group.split(':')
                            group_name = group_data[0]
                            user_ids = group_data[1].split(' ')

                            content += "\n\nh2. " + group_name + "\n\n"
                            for user in user_ids:
                                #contact = redmine.contact.get()
                                if user != '':
                                    contact = all_contacts.get(user.lower())

                                    if contact != None:

                                        content += "* {{contact(%s)}}: %s \n" % (contact.id, user)
                                    else:
                                        content += "* " + user + "\n"
                                        error_message = error_store.get(user,{})
                                        e_webauftritt = error_message.get('Webauftritt', [])
                                        e_webauftritt.append(project.identifier)
                                        e_group = error_message.get('Group',[])
                                        e_group.append(group_name)

                                        error_store[user] = {'Webauftritt': e_webauftritt, 'Group': e_group}


                    try: 
                        page = redmine.wiki_page.get('Fionagruppen',project_id=project.id)
                        redmine.wiki_page.update('Fionagruppen',
                                                 project_id=project.id,
                                                 title='Fionagruppen',
                                                 text=content)
                    except ResourceNotFoundError, e:
                        redmine.wiki_page.create(project_id=project.id,
                                                 title='Fionagruppen',
                                                 text=content)


                except ValidationError, e:
                    print "Error on {id} with error: {message}".format(id=fiona_id, message=e.message)
                except ResourceNotFoundError, e:
                    pass
        if error_store:
            error_message = """Folgende User sind unbekannt:

|_.Campus-Kennung |_.Fionagruppen |_.Projekte |
"""
            for message in error_store:
                error_message += '| {ck} | {groups} | {projects} |\n'.format(
                    ck=message, 
                    groups=', '.join(set(error_store[message]['Group'])), 
                    projects=', '.join(set(error_store[message]['Webauftritt']) ) ) 

            redmine.issue.create(
                project_id=redmine.project.get('webprojekte').id,
                subject="Unbekannte Nutzer bei Import " + datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
                description=error_message
                )

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_param = sys.argv[1]
        file_path = os.path.abspath(file_param)
        connect_projects_with_user(file_path)
