API Documentation
======================

.. automodule:: plugins.api
   :members:
   :private-members:
.. py:decorator:: plugin_method(help= None, callable_only=False)

    This decorator marks a function as a plugin function i.e. the server or user can call it.

    .. code-block:: python

        @plugin_init_function.plugin_method()
        def a_plugin_function(api):
            print("I can now be called from the chat")

    :param callable_only: Wether or not this function will be added to the text parser
    :param help: Explains what the function does
