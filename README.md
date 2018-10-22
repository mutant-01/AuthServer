# Centralized authentication and authorization
The authentication system expose four main endpoints:
* token: which accepts user credentials and issues token in response.
* revoke: revoke the token in authorization header by blacklisting it.
* authorize: used by other services to determine a token accessibility against specified resources.
* user_resources: used by the frontend application to determine which resources the user of the token has access.

### Authorize endpoint:
It is used by other services to make sure the provided token by the user has access to the requested resources. 
the authorize request json body should consist of the token and the list of the resources that the user has requested. 
example authorize request: 
```javascript
{
	"token": "the token",
	"resources": [ "auth:users:w", "auth:roles:r"]
}
````
the response to authorize request contains the token in the request and 
a dictionary the represents which resources are allowed to be used by the token.
the resources dictionary consists of resources path as keys and resources value as values, 
if resource value is null, the dictionary value would be True, representing a simple resource access without value.  
example authorize response:
```javascript
{
	"token": "the token",
	"resources": {"auth:users:w": true, "auth:roles:r": false}
}
````
### Resource name convention
Resource owners can register any resource name as resources are simple strings, they can use their own conventions.
but it is recommended that use the following convention:
'service_name:resource_name:access_level'
example: auth:users:w
### Identities:
one can manage roles and users and register resources via the HTTP API, the endpoints resources are as below:
##### manage users: 
URL_PREFIX:users:r 
URL_PREFIX:users:w 
##### manage roles:
URL_PREFIX:roles:r 
URL_PREFIX:roles:w 
##### manage resources:
URL_PREFIX:roles:r 
URL_PREFIX:roles:w 
##### assign roles to user:
URL_PREFIX:users:r 
URL_PREFIX:users:w 
URL_PREFIX:roles:r 
##### assign users to role:
URL_PREFIX:roles:r 
URL_PREFIX:roles:w 
URL_PREFIX:users:r 
##### assign resources to role:
URL_PREFIX:roles:r 
URL_PREFIX:roles:w 
URL_PREFIX:resources:r 
##### assign roles to resource:
URL_PREFIX:resources:r 
URL_PREFIX:resources:w 
URL_PREFIX:roles:r 
### Environment variables:
* DATABASE_URI: the postgres uri to connect to, default is: postgres://postgres@postgres:5432/auth 
mind the database name in the URI, the database should be created before starting the server.
* LOG_LEVEL: the level of logging
* LOG_PREFIX: the prefix of logging
* JWT_SECRET_KEY: required.
* JWT_ACCESS_TOKEN_EXPIRES: default is 10803,(in minutes)
* JWT_HEADER_NAME: default is 'Authorization'
* JWT_HEADER_TYPE: the prefix before token in authorization header, default is Bearer.
* REDIS_HOST: default is 'redis'
* REDIS_PORT: default is '6379'
* REDIS_BLACKLIST = the data structure name in redis to hold the revoked tokens, default is 'blacklist'
* URL_PREFIX: the prefix for service http routes, should be the service name. default is auth.
### running the AuthServer:
1. before starting the server one should create the database in postgres instance.
2. run the init.py script with admin username and password.
3. set the environment variables
### flask admin panel
an administrative panel is available under '/<URL_PREFIX>/admin/'
