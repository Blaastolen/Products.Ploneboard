## Controller Python Script "board_edit"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=title, description, id=''
##title=Edit a board
##

# if there is no id specified, keep the current one
if not id:
    id = context.getId()

new_context = context.portal_factory.doCreate(context, id)
new_context.processForm()

#new_context.edit( title=title
#                , description=description)
#new_context.plone_utils.contentEdit( new_context
#                                   , id=id
#                                   , description=description)

return state.set(context=new_context, portal_status_message='Board changes saved.')