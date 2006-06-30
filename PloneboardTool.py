from AccessControl import ClassSecurityInfo
import Globals
from OFS.Folder import Folder
from ZPublisher.HTTPRequest import FileUpload
from OFS.Image import File
from Products.CMFCore.ActionProviderBase import ActionProviderBase
from Products.CMFCore.utils import UniqueObject
from Products.CMFCore.permissions import ManagePortal, View
#from permissions import AddAttachment
from Products.CMFCore.utils import getToolByName
from ZODB.PersistentMapping import PersistentMapping
from Products.Ploneboard.utils import importModuleFromName
from Acquisition import aq_base
from Products.Ploneboard.config import PLONEBOARD_TOOL


class PloneboardTool(UniqueObject, Folder, ActionProviderBase):
    id = PLONEBOARD_TOOL
    meta_type = 'Ploneboard Tool'

    security = ClassSecurityInfo()
    def __init__(self):
        self.transforms = PersistentMapping()
    
    security.declarePrivate('registerTransform')
    def registerTransform(self, name, module, friendlyName=''):
        tr_tool = getToolByName(self, 'portal_transforms')
        if name not in tr_tool.objectIds():
            tr_tool.manage_addTransform(name, module)

        if name not in self.transforms:
            self.transforms[name] = {'enabled' : True, 
                                     'friendlyName' : friendlyName,
                                     }

    security.declarePrivate('unregisterTransform')
    def unregisterTransform(self, name):
        tr_tool = getToolByName(self, 'portal_transforms')
        tr_tool._delObject(name)
        self.transforms.remove(name)

    security.declareProtected(ManagePortal, 'enableTransform')
    def enableTransform(self, name, enabled=True):
        """Change the activity status for a transform."""
        self.transforms[name]['enabled'] = enabled

    security.declarePrivate('unregisterAllTransforms')
    def unregisterAllTransforms(self):
        tr_tool = getToolByName(self, 'portal_transforms')
        for transform_name in self.getTransforms():
            try:
                tr_tool._delObject(transform_name)
            except AttributeError, e:
                # _delObject couldn't find the transform_name. Must be gone already.
                pass
        self.transforms.clear()

    security.declareProtected(ManagePortal, 'getTransforms')
    def getTransforms(self):
        """ Returns list of transform names"""
        return self.transforms.keys()
    
    security.declareProtected(ManagePortal, 'getTransformFriendlyName')
    def getTransformFriendlyName(self, name):
        """ Returns a friendly name for the given transform"""
        return self.transforms[name]['friendlyName']
    
    security.declareProtected(View, 'getEnabledTransforms')
    def getEnabledTransforms(self):
        """ Returns list of names for enabled transforms"""
        return [name for name in self.transforms.keys() if self.transforms[name]['enabled']]

    security.declareProtected(View, 'performCommentTransform')
    def performCommentTransform(self, orig, **kwargs):
        """ This performs the comment transform - also used for preview """
        transform_tool = getToolByName(self, 'portal_transforms')
        
        # This one is very important, because transform object has no 
        # acquisition context inside it, so we need to pass it our one
        context=kwargs.get('context', self)

        data = transform_tool._wrap('text/plain')
        
        for transform in self.getEnabledTransforms():
            data = transform_tool.convert(transform, orig, data, context)
            orig = data.getData()
        
        orig = orig.replace('\n', '<br/>')
        return orig

    # File upload - should be in a View once we get formcontroller support in Views
    security.declareProtected(View, 'getUploadedFiles')
    def getUploadedFiles(self):
        request = self.REQUEST

        result = []
        files = request.get('files', [])
        
        if not files:
            return []

        sdm = getToolByName(self, 'session_data_manager', None)
        
        if sdm is not None:        
            pt = getToolByName(self, 'plone_utils')
            hassession = sdm.hasSessionData()

            for file in files:
                if isinstance(file, basestring) and hassession:
                    # Look it up from session
                    oldfile = request.SESSION.get(file, None)
                    if oldfile is not None:
                        result.append(oldfile)
                if isinstance(file, FileUpload):
                    if file:
                        id = pt.normalizeString(file.filename)
                        ct=file.headers.getheader('content-type')
                        if ct is None:
                            ct=''
                        newfile = File(id, file.filename, file, ct)
                        request.SESSION[id] = newfile
                        result.append(newfile)

            # delete files form session if not referenced
            new_filelist = [x.getId() for x in result]
            old_filelist = hassession and request.SESSION.get('ploneboard_uploads', []) or []
            for removed in [f for f in old_filelist if f not in new_filelist]:
                del request.SESSION[f]
            if hassession or new_filelist:
                request.SESSION['ploneboard_uploads'] = new_filelist
            
        return result

    security.declareProtected(View, 'clearUploadedFiles')
    def clearUploadedFiles(self):
        # Get previously uploaded files with a reference in request
        # + files uploaded in this request
        # XXX ADD VARIABLE THAT KEEPS TRACK OF FILE NAMES
        request = self.REQUEST

        sdm = getToolByName(self, 'session_data_manager', None)
        
        if sdm is not None:
            if sdm.hasSessionData():
                old_filelist = request.SESSION.get('ploneboard_uploads', None)
                if old_filelist is not None:
                    for file in old_filelist:
                        if request.SESSION.has_key(file):
                            del request.SESSION[file]
                    del request.SESSION['ploneboard_uploads']


Globals.InitializeClass(PloneboardTool)
