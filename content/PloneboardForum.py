"""
$Id$
"""

# zope3, zope 2.8, or Five dependency
from zope.interface import implements
from zope.interface import Interface

from Products.Five.bridge import fromZ2Interface

from random import randint

import sys
import Globals
from AccessControl import ClassSecurityInfo
from Acquisition import aq_base, aq_chain, aq_inner
from DateTime import DateTime
from OFS.Image import File

from BTrees.Length import Length

from Products.ZCatalog.Lazy import LazyMap

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.permissions import ModifyPortalContent

from Products.CMFPlone.utils import _createObjectByType
from Products.Archetypes.public import BaseBTreeFolderSchema, Schema
from Products.Archetypes.public import TextField, BooleanField, LinesField, IntegerField
from Products.Archetypes.public import BaseBTreeFolder, registerType
from Products.Archetypes.public import TextAreaWidget, BooleanWidget, MultiSelectionWidget, IntegerWidget, SelectionWidget
from Products.Archetypes.public import DisplayList

from Products.Ploneboard.config import PROJECTNAME, HAS_SIMPLEATTACHMENT
from Products.Ploneboard.permissions import ViewBoard, SearchBoard, \
     AddForum, ManageForum, ManageBoard, AddConversation, ModerateForum
from PloneboardConversation import PloneboardConversation
from Products.Ploneboard.interfaces import IPloneboard, IForum, IConversation
    
from Products.CMFPlone.interfaces.NonStructuralFolder \
    import INonStructuralFolder as ZopeTwoINonStructuralFolder
try:
    from Products.CMFPlone.interfaces.structure import INonStructuralFolder
except ImportError:
    INonStructuralFolder = fromZ2Interface(ZopeTwoINonStructuralFolder)

    
schema = BaseBTreeFolderSchema + Schema((
    TextField('description',
              searchable = 1,
              default_content_type = 'text/html',
              default_output_type = 'text/plain',
              widget = TextAreaWidget(
                        description = "Brief description of the forum topic.",
                        description_msgid = "help_description_forum",
                        label = "Description",
                        label_msgid = "label_description_forum",
                        i18n_domain = "ploneboard",
                        rows = 5)),

    LinesField('category',
                 write_permission = ManageForum,
                 vocabulary = 'getCategories',
                 widget = MultiSelectionWidget(
                            description = "Select which category the forum should be listed under. A forum can exist in multiple categories, although using only one category is recommended.",
                            description_msgid = "help_category",
                            condition="object/getCategories",
                            label = "Category",
                            label_msgid = "label_category",
                            i18n_domain = "ploneboard",
                          )),
    IntegerField('maxAttachments',
                write_permission = ManageForum,
                default = 1,
                widget = IntegerWidget(
                         description = "Select the maximum number of attachments per comment.",
                         description_msgid = "help_maxattachments",
                         label = "Maximum number of attachments",
                         label_msgid = "label_maxattachments",
                         i18n_domain = "ploneboard",
                )),
    IntegerField('maxAttachmentSize',
                write_permission = ManageForum,
                vocabulary = 'getAttachmentSizes',
                default = 100,
                widget = SelectionWidget(
                         description = "Select the maximum size for attachments.",
                         description_msgid = "help_maxattachmentsize",
                         label = "Maximum attachment size",
                         label_msgid = "label_maxattachmentsize",
                         i18n_domain = "ploneboard",
                )),
    ))


if not HAS_SIMPLEATTACHMENT:
    schema['maxAttachments'].mode="r"
    schema['maxAttachments'].default=0
    schema['maxAttachments'].widget.visible={'edit' : 'invisible', 'view' : 'invisible' }
    schema['maxAttachmentSize'].widget.visible={'edit' : 'invisible', 'view' : 'invisible' }


class PloneboardForum(BaseBTreeFolder):
    """A Forum contains conversations."""
    implements(IForum, INonStructuralFolder)
    __implements__ = (BaseBTreeFolder.__implements__, ZopeTwoINonStructuralFolder)

    meta_type = 'PloneboardForum'
    archetype_name = 'Forum'
    
    schema = schema

    content_icon = 'ploneboard_forum_icon.gif'
    allowed_content_types = ('PloneboardConversation',)
    global_allow = 0 # To avoid it showing in the add content menu
    default_view = ''

    _at_rename_after_creation = True

    actions = (
            { 'id'          : 'view'
            , 'name'        : 'View'
            , 'action'      : 'string:$object_url'
            , 'permissions' : (ViewBoard,)
            },
            { 'id'          : 'edit'
            , 'name'        : 'Edit'
            , 'action'      : 'string:$object_url/edit'
            , 'permissions' : (ModifyPortalContent,)
            },
            { 'id'          : 'metadata'
            , 'name'        : 'Properties'
            , 'action'      : 'string:$object_url/properties'
            , 'permissions' : (ModifyPortalContent,)
            },
            { 'id'          : 'rssfeed'
            , 'name'        : 'RSS Feed'
            , 'action'      : 'string:$object_url/rss-properties'
            , 'permissions' : (ManageBoard,)
            },
            { 'id'          : 'local_roles'
            , 'name'        : 'Sharing'
            , 'action'      : 'string:$object_url/sharing'
            , 'permissions' : (ManageBoard,)
            },
            { 'id'          : 'moderate'
            , 'name'        : 'Moderate'
            , 'action'      : 'string:$object_url/moderate'
            , 'permissions' : (ModerateForum,)
            },
        )

    aliases = \
        {
              '(Default)'      : 'forum_view', 
              'view'           : 'forum_view',
              'edit'           : 'base_edit',
              'properties'     : 'base_metadata',
              'sharing'        : 'folder_localrole_form',
              'rss-properties' : 'editSynProperties',
              'moderate'       : 'moderation_form',
        }

    security = ClassSecurityInfo()
    
    def getCatalog(self):
        return getToolByName(self, 'portal_catalog')

    security.declareProtected(ManageForum, 'edit')
    def edit(self, **kwargs):
        """Alias for update()
        """
        self.update(**kwargs)

    security.declarePublic('synContentValues')
    def synContentValues(self):
        return (self.getConversations())
    
    security.declareProtected(ViewBoard, 'getBoard')
    def getBoard(self):
        """Returns containing or nearest board."""
        # Try containment
        stoptypes = ['Plone Site']
        for obj in aq_chain(aq_inner(self)):
            if hasattr(obj, 'portal_type') and obj.portal_type not in stoptypes:
                if IPloneboard.providedBy(obj):
                    return obj

        return None

    security.declareProtected(AddConversation, 'addConversation')
    def addConversation(self, title, text=None, creator=None, files=None, **kwargs):
        """Adds a new conversation to the forum.
        
        XXX should be possible to parameterise the exact type that is being 
        added.
        """
        
        id = self.generateId(prefix='')

        conv = _createObjectByType('PloneboardConversation', self, id)
        
        # XXX: There is some permission problem with AT write_permission
        # and using **kwargs in the _createObjectByType statement. 
        conv.setTitle(title)
        
        if creator is not None:
            conv.setCreators([creator])
        

        if text is not None:
            m = _createObjectByType('PloneboardComment', conv, conv.generateId(prefix=''))
            
            # XXX: There is some permission problem with AT write_permission
            # and using **kwargs in the _createObjectByType statement. 
            m.setTitle(title)
            m.setText(text)
            
            if creator is not None:
                m.setCreators([creator])

            # Create files in message
            if files:
                for file in files:
                    # Get raw filedata, not persistent object with reference to tempstorage
                    attachment = File(file.getId(), file.title_or_id(), str(file.data), file.getContentType())
                    m.addAttachment(attachment)
                    
            m.reindexObject()

        conv.reindexObject()
        return conv

    security.declareProtected(ViewBoard, 'getConversation')
    def getConversation(self, conversation_id, default=None):
        """Returns the conversation with the given conversation id."""
        #return self._getOb(conversation_id, default)
        catalog = self.getCatalog()
        conversations = catalog(
        object_implements='Products.Ploneboard.interfaces.IConversation', 
        getId=conversation_id, 
        path='/'.join(self.getPhysicalPath()))
        if conversations:
            return conversations[0].getObject()
        else:
            return None
    
    security.declareProtected(ManageForum, 'removeConversation')
    def removeConversation(self, conversation_id):
        """Removes a conversation with the given conversation id from the forum."""
        self._delObject(conversation_id)
    
    security.declareProtected(ViewBoard, 'getConversations')
    def getConversations(self, limit=20, offset=0):
        """Returns conversations."""
        catalog = self.getCatalog()
        return [f.getObject() for f in \
                catalog(object_implements='Products.Ploneboard.interfaces.IConversation', 
                        sort_on='modified', 
                        sort_order='reverse', 
                        sort_limit=(offset+limit), 
                        path='/'.join(self.getPhysicalPath()))[offset:offset+limit]]

    security.declareProtected(ViewBoard, 'getNumberOfConversations')
    def getNumberOfConversations(self):
        """Returns the number of conversations in this forum."""
        return len(self.getCatalog()(
        object_implements='Products.Ploneboard.interfaces.IConversation',
        path='/'.join(self.getPhysicalPath())))

    security.declareProtected(ViewBoard, 'getNumberOfComments')
    def getNumberOfComments(self):
        """Returns the number of comments to this forum."""
        return len(self.getCatalog()(
        object_implements='Products.Ploneboard.interfaces.IComment',
        path='/'.join(self.getPhysicalPath())))

    security.declareProtected(ViewBoard, 'getLastConversation')
    def getLastConversation(self):
        """
        Returns the last conversation.
        """
        # XXX Is Created or Modified the most interesting part?
        res = self.getCatalog()(
        object_implements='Products.Ploneboard.interfaces.IConversation',
        sort_on='created', sort_order='reverse', sort_limit=1,
        path='/'.join(self.getPhysicalPath()))
        if res:
            return res[0].getObject()
        else:
            return None

    security.declareProtected(ViewBoard, 'getLastCommentDate')
    def getLastCommentDate(self):
        """
        Returns a DateTime corresponding to the timestamp of the last comment 
        for the forum.
        """
        res = self.getCatalog()(
        object_implements='Products.Ploneboard.interfaces.IComment',
        sort_on='created', sort_order='reverse', sort_limit=1,
        path='/'.join(self.getPhysicalPath()))
        if res:
            return res[0].created
        else:
            return None

    security.declareProtected(ViewBoard, 'getLastCommentAuthor')
    def getLastCommentAuthor(self):
        """
        Returns the name of the author of the last comment.
        """
        res = self.getCatalog()(
        object_implements='Products.Ploneboard.interfaces.IComment',
        sort_on='created', sort_order='reverse', sort_limit=1,
        path='/'.join(self.getPhysicalPath()))
        if res:
            return res[0].Creator
        else:
            return None

    # Vocabularies
    security.declareProtected(ViewBoard, 'getCategories')
    def getCategories(self):
        value = []
        board = self.getBoard()
        if board is not None and hasattr(board, 'getCategories'):
            categories = board.getCategories()
            if categories is not None:
                value = [(c,c) for c in categories]
        value.sort()
        return DisplayList(value)

    security.declareProtected(ViewBoard, 'getAttachmentSizes')
    def getAttachmentSizes(self):
        voc = DisplayList()
        voc.add('10', '10 kilobyte')
        voc.add('100', '100 kilobyte')
        voc.add('1000', '1 megabyte')
        voc.add('10000', '10 megabyte')
        voc.add('-1', 'unlimited')

        return voc


    ############################################################################
    # Folder methods, indexes and such

    def __nonzero__(self):
        return 1


registerType(PloneboardForum, PROJECTNAME)
