"""
$Id$
"""

from Globals import package_home
from Products.Archetypes.public import process_types, listTypes
from Products.Archetypes.ArchetypeTool import getType
from Products.CMFCore.DirectoryView import registerDirectory
from Products.Ploneboard.PloneboardTool import PloneboardTool
from Products.Ploneboard.PloneboardCatalog import PloneboardCatalog
try:
    from Products.CMFPlone.interfaces import IPloneSiteRoot
    from Products.GenericSetup import EXTENSION, profile_registry
    HAS_GENERICSETUP = True
except ImportError:
    HAS_GENERICSETUP = False

import sys, os, os.path


from config import SKINS_DIR, GLOBALS, PROJECTNAME

# PloneboardWorkflow requires GLOBALS
import PloneboardWorkflow

registerDirectory(SKINS_DIR, GLOBALS)

def initialize(context):
    ##Import Types here to register them
    from content import Ploneboard, PloneboardForum, PloneboardConversation, PloneboardComment

    # If we put this import line to the top of module then
    # utils will magically point to Ploneboard.utils
    from Products.CMFCore import utils
    utils.ToolInit('Ploneboard Tool', 
            tools=(PloneboardTool, PloneboardCatalog ), 
            icon='tool.gif'
            ).initialize(context)

    content_types, constructors, ftis = process_types(
        listTypes(PROJECTNAME),
        PROJECTNAME)

    # Assign an own permission to all content types
    # Heavily based on Bricolite's code from Ben Saller
    import permissions as perms

    allTypes = zip(content_types, constructors)
    for atype, constructor in allTypes:
        kind = "%s: %s" % (PROJECTNAME, atype.archetype_name)
        utils.ContentInit(
            kind,
            content_types      = (atype,),
            # Add permissions look like perms.Add{meta_type}
            permission         = getattr(perms, 'Add%s' % atype.meta_type),
            extra_constructors = (constructor,),
            fti                = ftis,
            ).initialize(context)

    if HAS_GENERICSETUP:
        profile_registry.registerProfile('Ploneboard',
                    'PloneBoard',
                    'Extension profile for default Ploneboard setup',
                    'profiles/default',
                    'Ploneboard',
                    EXTENSION,
                    for_=IPloneSiteRoot)


# Avoid breaking old Ploneboard instances when moving content types modules
# from Ploneboard/types/ to Ploneboard/content/
import content
sys.modules['Products.Ploneboard.types'] = content
