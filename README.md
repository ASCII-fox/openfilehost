# Open File Host 

Simple ad-hoc file sharing and hosting via a web interface on an ipv6 address.

# Usage instructions 

1. Ensure that system dependencies are installed
2. Change configuration options as needed in ```server-config.toml``` and ensure relevant ports are open
3. Run START-SERVER.sh
4. If ```shouldserverbepublic``` is set to 1, the interface will be available at the HTTPS url (https://[Your IPV6 address here]:https_port). Otherwise, it will be accessible on the LAN via your ipv4 address through http.

# System dependencies 
```
Python 3 or later - Python environment with relevant packages is setup automatically when running START-SERVER.sh 
OpenSSL - Certificate generation
```

Should work out of the box on most Linux systems. No guarantee with regards to functionality on Windows systems.

# Folders
```
database - Handles file and database operations 
python - Mainly helpers and certificate functions
ssl - SSL certificate generation and storage 
static - served web interfaces. Mounted by the server.
upload - generated directory for uploaded files. Managed by database.py
```
