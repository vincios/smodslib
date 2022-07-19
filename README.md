# smodslib: a Skymods.ru abstraction plugin

smods abstracts the Skymods.ru mods catalogue site and helps you to search and downloads mods from it.

It uses BeautifulSoup to scrape the website and abstract it to a set of objects.


## Get started
All the most common used methods are exported by the 'smodslib' module, so for a simple ues you can write something like

'''

'''

## Model
Mods are abstracted in a set of Mod objects based on their purpose.

### ModBase
ModBase is the base class from all others Mods type derives from. It contains all the information that a mod must have
always. Other Mods objects are build on top of a ModBase object, adding other information accorgind its scope.

