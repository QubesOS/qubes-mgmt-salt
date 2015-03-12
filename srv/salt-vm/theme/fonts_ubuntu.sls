#!yamlscript

##
# fonts-ubuntu
##

$with /usr/share/fonts/ubuntu-font-family:
  file.recurse:
    - source: salt://theme/files/fonts/ubuntu-font-family-0.80
    - clean: False
    - user: root
    - group: root
    - dir_mode: 755
    - file_mode: 644

  $if grains('os') == 'Fedora':
    $with ttmkfdir -o /usr/share/fonts/ubuntu-font-family/fonts.scale -d /usr/share/fonts/ubuntu-font-family > /usr/share/fonts/ubuntu-font-family/fonts.dir && fc-cache -fv:
      cmd.run: 
        - creates: 
          - /usr/share/fonts/ubuntu-font-family/fonts.dir
          - /usr/share/fonts/ubuntu-font-family/fonts.scale

# Debian 
# Rebuilds fonts cache
# fc-cache -fv  rebuilds cached list of fonts 

# Remove ubuntu directory if it exists (old naming format)
/usr/share/fonts/ubuntu:
  file.absent: []

