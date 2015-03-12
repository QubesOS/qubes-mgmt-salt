#!yamlscript
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

$python: |
    from salt://salt/map.sls import SaltMap

$with certificate-dependencies:
  pkg.installed:
    - name: $SaltMap.python_openssl

  # Create a Certificate Authority (CA)
  $with salt-call --local tls.create_ca minion:
    cmd.run:
      - creates: /etc/pki/minion/minion_ca_cert.crt

    # Create a Certificate Signing Request (CSR) for a particular Certificate Authority (CA)
    $with salt-call --local tls.create_csr minion:
      cmd.run:
        - creates: /etc/pki/minion/certs/localhost.csr

      # Create a Certificate Authority (CA)
      salt-call --local tls.create_ca_signed_cert minion localhost:
        cmd.run:
          - creates: /etc/pki/minion/certs/localhost.crt

  # Create a Self-Signed Certificate (CERT)
  # /etc/pki/tls/certs/localhost.*
  $with salt-call --local tls.create_self_signed_cert:
    cmd.run:
      - creates: /etc/pki/tls/certs/localhost.crt

# Create a .pem file for web server
cat localhost.crt > localhost.pem; cat localhost.key >> localhost.pem:
  cmd:
    - run
    - onlyif: /bin/bash -c "[[ /etc/pki/tls/certs/localhost.crt -nt /etc/pki/tls/certs/localhost.pem ]]"
    - cwd: /etc/pki/tls/certs
