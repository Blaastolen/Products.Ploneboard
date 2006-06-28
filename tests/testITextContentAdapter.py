#
# Comment tests
#

from Products.Ploneboard.tests import PloneboardTestCase, utils
from Products.Ploneboard.interfaces import IComment
from Products.Ploneboard.content.PloneboardComment import PloneboardComment

from OFS.Image import File
from Products.CMFPlone.utils import _createObjectByType

class TestITextContentAdapter(PloneboardTestCase.PloneboardTestCase):

    def afterSetUp(self):
        utils.caSetUp(self)
        from Products.ATContentTypes.z3.interfaces import ITextContent 
        self.board = _createObjectByType('Ploneboard', self.folder, 'board')
        self.forum = _createObjectByType('PloneboardForum', self.board, 'forum')
        self.conv = self.forum.addConversation('conv1', 'conv1 body')
        
        self.comment = self.conv.objectValues()[0]
        self.textContent = ITextContent(self.comment)
        
    def beforeTearDown(self):
        utils.caTearDown(self)

    def testGetText(self):
        self.assertEqual(self.comment.getText(), 
                         self.textContent.getText())
    
    def testSetText(self):
        s = 'blah'
        self.textContent.setText('blah')
        
        self.assertEqual(self.comment.getText(), s)
        self.assertEqual(self.textContent.getText(), s)
        
    def testCookedBody(self):
        self.assertEqual(self.textContent.CookedBody(), 
                         self.comment.getText())

    def testEditableBody(self):
        self.assertEqual(self.textContent.CookedBody(), 
                         self.comment.getRawText())


if __name__ == '__main__':
    framework()
else:
    import unittest
    def test_suite():
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(TestITextContentAdapter))
        return suite
