import urllib
from zope import interface
from Products import Five
from Products.CMFCore import utils as cmf_utils
from Products.Ploneboard import permissions
from Products.Ploneboard.batch import Batch
from Products.Ploneboard.interfaces import IConversationView, ICommentView

class CommentViewableView(Five.BrowserView):
    """Any view that might want to interact with comments should inherit
    from this base class.
    """
    
    def __init__(self, context, request):
        Five.BrowserView.__init__(self, context, request)

        self.portal_actions = cmf_utils.getToolByName(self.context, 'portal_actions')
        self.plone_utils = cmf_utils.getToolByName(self.context, 'plone_utils')
        self.portal_membership = cmf_utils.getToolByName(self.context, 'portal_membership')
        self.portal_workflow = cmf_utils.getToolByName(self.context, 'portal_workflow')

    def _buildDict(self, comment):
        """Produce a dict representative of all the important properties
        of a comment.
        """
        
        checkPermission = self.portal_membership.checkPermission
        actions = self.portal_actions.listFilteredActionsFor(comment)

        res= {
                'Title': comment.title_or_id(),
                'Creator': comment.Creator(),
                'creation_date': comment.CreationDate(),
                'getId': comment.getId(),
                'getText': comment.getText(),
                'absolute_url': comment.absolute_url(),
                'getAttachments': comment.getAttachments(),
                'canEdit': checkPermission(permissions.EditComment, comment),
                'canDelete': checkPermission(permissions.DeleteComment, comment),
                'canReply': checkPermission(permissions.AddComment, comment),
                'getObject': comment,
                'workflowActions' : actions['workflow'],
                'review_state' : self.portal_workflow.getInfoFor(comment, 'review_state'),
                'reviewStateTitle' : self.plone_utils.getReviewStateTitleFor(comment),
                'UID': comment.UID(),
            }
        return res
        
class CommentView(CommentViewableView):
    """A view for getting information about one specific comment.
    """
    
    interface.implements(ICommentView)
    
    def comment(self):
        return self._buildDict(self.context)

    def author(self):
        creator = self.context.Creator()
        info = self.portal_membership.getMemberInfo(creator)
        if info is None:
            return creator
        return info.get('fullname', creator)

    def quotedBody(self):
        text = self.context.getText()
        if text:
            return '<p>Previously %s wrote:</p>' \
                   '<blockquote>%s</blockquote><p></p>' % \
                   (self.author(), self.context.getText())
        else:
            return ''

class ConversationView(CommentView):
    """A view component for querying conversations.
    """
    
    interface.implements(IConversationView)

    def conversation(self):
        checkPermission = self.portal_membership.checkPermission
        conv = self.context
        forum = conv.getForum()

        return {
                'maximumAttachments' : forum.getMaxAttachments(),
                'canAttach': forum.getMaxAttachments()>0 and \
                              checkPermission(permissions.AddAttachment,conv),
                }

    def comments(self):
        batchSize = 30
        batchStart = int(self.request.get('b_start', 0))
        numComments = self.context.getNumberOfComments()
        return Batch(self._getComments, numComments, batchSize, batchStart, orphan=1)    
    
    def root_comments(self):
        rootcomments =  self.context.getRootComments()
        for ob in rootcomments:
            yield self._buildDict(ob)

    def children(self, comment):
        if type(comment) is dict:
            comment = comment['getObject']
        
        for ob in comment.getReplies():
            yield self._buildDict(ob)
    
    def _getComments(self, limit, offset):
        """Dictify comments before returning them to the batch
        """
        return [self._buildDict(ob) for ob in self.context.getComments(limit=limit, offset=offset)]

class DeleteCommentView(Five.BrowserView):
    """Delete the current comment.  If the comment is the root comment
    of a conversation, delete the entire conversation instead.
    """
    
    def __call__(self):
        redirect = self.request.response.redirect
        comment = self.context
        conversation = comment.getConversation()

        if len(conversation.getComments()) == 1:
            forum = conversation.getForum()
            conversation.delete()
            msg = urllib.quote('Conversation deleted')
            redirect(forum.absolute_url()+'?portal_status_message='+msg)
        else:
            comment.delete()
            msg = urllib.quote('Comment deleted')
            redirect(conversation.absolute_url()+'?portal_status_message='+msg)
