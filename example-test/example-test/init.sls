create-file:
  file.touch: 
    - name: /tmp/test-file

append-file:
  file.append:
    - name: /tmp/test-file
    - text: Just a test
    - require:
      - file: create-file