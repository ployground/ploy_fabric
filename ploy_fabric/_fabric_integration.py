from __future__ import unicode_literals


def connect(self, key):
    import fabric.network
    import fabric.state
    import paramiko
    r = fabric.network.parse_host_string(key)
    user = r['user'] or 'root'
    host = r['host']
    server = fabric.state.env.instances[host]
    try:
        ssh_info = server.init_ssh_key(user=user)
    except paramiko.SSHException as e:
        from ploy_fabric import log
        import sys
        log.error("Couldn't validate fingerprint for ssh connection.")
        log.error(e)
        log.error("Is the server finished starting up?")
        sys.exit(1)
    self[key] = ssh_info['client']


def patch():
    import fabric.network
    fabric.network.HostConnectionCache.connect = connect
