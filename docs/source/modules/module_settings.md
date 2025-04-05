# Settings Documentation

This module contains all settings that define the servers behaviour. They can roughly be categorized into

* Django settings
* Plugin system settings
* miscellaneous

For all django specific settings look at [this](https://docs.djangoproject.com/en/4.1/topics/settings/)
and [this](https://docs.djangoproject.com/en/4.1/ref/settings/).

The plugin and miscellaneous settings should be documented. Those that aren't are best left alone.
For settings specific to individual plugins read up on the plugin tutorial. 

Most settings are available via the generated config.ini. However not all of them (most of the time
that is on purpose).

Every setting specified in the config.ini *or in the settings.py itself* can be overriden by setting
an environment variable with the same name.


```{eval-rst}  
.. automodule:: RIXAWebserver.settings
   :members:
   :no-value:
   :undoc-members:
```


