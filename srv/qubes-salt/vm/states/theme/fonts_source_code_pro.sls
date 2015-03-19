#!yamlscript

##
# fonts-source-code-pro
##

$with /usr/share/fonts/source-code-pro:
  file.recurse:
    - source: salt://theme/files/fonts/source-code-pro
    - clean: False
    - user: root
    - group: root
    - dir_mode: 755
    - file_mode: 644
  
  $if grains('os') == 'Fedora':
    $with ttmkfdir -o /usr/share/fonts/source-code-pro/fonts.scale -d /usr/share/fonts/source-code-pro > /usr/share/fonts/source-code-pro/fonts.dir && fc-cache -fv:
      cmd.run: 
        - creates: 
          - /usr/share/fonts/source-code-pro/fonts.dir
          - /usr/share/fonts/source-code-pro/fonts.scale

# Remove SourceCodePro directory if it exists (old naming format)
/usr/share/fonts/SourceCodePro:
  file.absent: []

# Remove Source_Code_Pro directory if it exists (old naming format)
/usr/share/fonts/Source_Code_Pro:
  file.absent: []

# Remove Source-Code-Pro directory if it exists (old naming format)
/usr/share/fonts/Source-Code-Pro:
  file.absent: []

