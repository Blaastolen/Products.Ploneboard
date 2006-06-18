from Products.CMFCore import permissions
from Products.CMFCore.permissions import setDefaultRoles


# Gathering Ploneboard Permissions into one place
RequestReview = permissions.RequestReview
# Add permissions differ for each type, and are imported by __init__.initialize
# so don't change their names!

# Separate view permission creates havoc
#ViewBoard = 'Ploneboard: View'
ViewBoard = permissions.View
SearchBoard = 'Ploneboard: Search'
AddBoard = AddPloneboard = 'Ploneboard: Add Ploneboard'
ManageBoard = 'Ploneboard: Add Ploneboard'


AddForum = AddPloneboardForum = 'Ploneboard: Add Forum'
ManageForum = 'Ploneboard: Add Forum'

AddConversation = AddPloneboardConversation = 'Ploneboard: Add Conversation'
ManageConversation = 'Ploneboard: Manage Conversation'

AddComment = AddPloneboardComment = 'Ploneboard: Add Comment'
EditComment = 'Ploneboard: Edit Comment'
AddAttachment = AddPloneboardAttachment = 'Ploneboard: Add Comment Attachment'
ManageComment = 'Ploneboard: Manage Comment'
ApproveComment = 'Ploneboard: Approve Comment' # Used for moderation
RetractComment = 'Ploneboard: Retract Comment'

# Note: if this changes, you must also change configure.zcml!
DeleteComment = permissions.ManagePortal 


# Set up default roles for permissions
setDefaultRoles(ViewBoard,
                ('Anonymous', 'Member', 'Manager'))

setDefaultRoles(SearchBoard,
                ('Anonymous', 'Member', 'Manager'))

setDefaultRoles(AddBoard,
                ('Manager', 'Owner'))

setDefaultRoles(ManageBoard,
                ('Manager', 'Owner'))

setDefaultRoles(AddConversation,
                ('Authenticated', 'Manager'))

setDefaultRoles(AddComment,
                ('Authenticated', 'Manager'))

setDefaultRoles(EditComment,
                ('Manager',))

setDefaultRoles(AddAttachment,
                ('Manager',))

setDefaultRoles(ManageConversation,
                ('Manager',))

setDefaultRoles(ManageComment,
                ('Manager',))

setDefaultRoles(ApproveComment,
                ('Manager',))

setDefaultRoles(RetractComment,
                ('Manager',))
