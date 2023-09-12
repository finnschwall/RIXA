# Issues

## Hard to do
These are not trivially fixable.

* __Resource tracker counts wrong for non-forked processes__

	There is no actual memory leak but just a problem in the python standard library with shared memory 
	objects. It originates in cases where the memory shared does not originate from a common parent 
	process (see [Issue 45209](https://bugs.python.org/issue45209) and [Issue 38119](https://bugs.python.org/issue38119)).
    An easy fix would be excluding non unix based systems. Since that is not an option and the error is
	harmless it will probably stay for now.
* __importlib.abc.MetaPathFinder not part of the standard library in all versions__
  
	Import hook therefore fails mostly with python > 3.9. Surprisingly that doesn't affect the server
  	but only the dev environment. Probably a future statement hidden in django somewhere. Fix is somewhat
	important before letting someone develop plugins as it can cause a lot of confusion.
## Normal
These are known and should be fixed as soon as time allows it.
* __Streams, pipes and Log__

	Currently all output gets mashed into the process that starts the server. Can be confusing also there could
	be a concurrency issues if logging into a file is activated.

## Further research required
Something I saw but am not yet sure if it is a continuing problem or just a problem with specific conditions
* __autoreload__

	I think there may be a problem with correctly shutting down all worker and plugin processes and threads.
	The relevant errors however occur very seldom.

## Potential
These ones I suspect could occur but have not tested the relevant modules thoroughly enough to confirm
* `from plugins.api import *` or `from plugins import api` or `import plugins.api as X` may not all lead to
equal success in loading and/or executing a plugin. Although im fairly certain the last one leads to problems.

## Misc



