# nativeconfig

Developers of cross-platform applications often face problems when application should interact with the system.  
And config files are no exception, since every popular OS has its own format and guidelines.

This package addresses this very problem in an elegant and Pythonic way:

    import os
    from nativeconfig import PreferredConfig, Option, ChoiceOption, IntOption

    class SuperbConfig(PreferredConfig):
        REGISTRY_PATH = r'Software\MyApp'
        JSON_PATH = os.path.expanduser('~/.config/MyApp/config')
        
        name = Option('Name')
        sex = ChoiceOption('Sex', ['male', 'female'], default='female')
        favorite_number = IntOption('FavoriteNumber', default=42)

We just created a config that will use appropriate locations on Windows, Mac OS X and Linux!
