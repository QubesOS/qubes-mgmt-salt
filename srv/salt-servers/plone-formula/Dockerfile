FROM      martinhoefling/salt-minion:debian
MAINTAINER Martin Hoefling <martin.hoefling@gmx.de>

# push formula
ADD plone /srv/salt/plone
ADD pillar.example /srv/pillar/example.sls
RUN echo "file_client: local" > /etc/salt/minion.d/local.conf
RUN echo "base:" > /srv/pillar/top.sls
RUN echo "  '*':" >> /srv/pillar/top.sls
RUN echo "    - example" >> /srv/pillar/top.sls
RUN salt-call --local state.sls plone.user | tee log.txt && grep "Failed:    0" log.txt
# we allow failing 1 state since setting a service on bootup doesnt work in docker
RUN salt-call --local state.sls plone | tee log.txt && grep "Failed:    1" log.txt