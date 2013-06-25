# Just a simple salt.client wrapper so that you can see what results it returns.

import sys, string
import salt.client

target = sys.argv[1]
command = string.join(sys.argv[2:])

client = salt.client.LocalClient()

result = client.cmd(target, "cmd.run", [command])
print result

