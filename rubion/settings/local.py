LOGGING = {
    'version' : 1,
    'disable_existing_loggers': False,
    'handlers' : {
        'cron': {
            'level' : 'INFO',
            'class' : 'logging.FileHandler',
            'filename' : '../logs/cronjobs/info.log'
        }
    },
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{asctime} {levelname} {message}',
            'style': '{',
        }
    },
    'loggers' : {
        'warn_projects' : {
            'handlers' : [ 'cron' ],
            'level': 'INFO',
            'propagate' : True,
            'formatter' : 'simple'
        }
    }
}
