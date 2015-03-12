{% from "plone/map.jinja" import plone with context %}

user_{{ plone.user }}:
  user.present:
    - name: {{ plone.user }}

group_{{ plone.group }}:
  group.present:
    - name: {{ plone.group }}
    