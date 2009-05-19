############################################################################
##
## Copyright (C) 2006-2009 University of Utah. All rights reserved.
##
## This file is part of VisTrails.
##
## This file may be used under the terms of the GNU General Public
## License version 2.0 as published by the Free Software Foundation
## and appearing in the file LICENSE.GPL included in the packaging of
## this file.  Please review the following to ensure GNU General Public
## Licensing requirements will be met:
## http://www.opensource.org/licenses/gpl-license.php
##
## If you are unsure which license is appropriate for your use (for
## instance, you are interested in developing a commercial derivative
## of VisTrails), please contact us at vistrails@sci.utah.edu.
##
## This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
## WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
##
############################################################################

from PyQt4 import QtCore, QtGui
from core import system
from core.modules.module_configure import StandardModuleConfigurationWidget
from core.modules.tuple_configuration import PortTableConfigurationWidget, \
    PortTable
from core.utils import PortAlreadyExists
from core.vistrail.module_function import ModuleFunction
from core.vistrail.module_param import ModuleParam
import urllib

class PythonHighlighter(QtGui.QSyntaxHighlighter):
    def __init__( self, document ):
        QtGui.QSyntaxHighlighter.__init__( self, document )
        self.rules = []
        
        keywordFormat = QtGui.QTextCharFormat()
        keywordFormat.setForeground(QtCore.Qt.blue)
        self.rules += [(r"\b%s\b"%w, keywordFormat, -1, -1, False)
                       for w in ["def","from", 
                                 "import","for","in", 
                                 "while","True","None",
                                 "False","pass","return",
                                 "self","tuple","list",
                                 "print","if","else",
                                 "elif","len","string"
                                 "assert","try","except",
                                 "exec", "break", "continue",
                                 "not", "and", "or", "as",
                                 "type", "int", "float",
                                 ]]
        
        defclassFormat = QtGui.QTextCharFormat()
        defclassFormat.setForeground(QtCore.Qt.blue)
        self.rules += [(r"\bclass\b\s*(\w+)", defclassFormat, -1, -1, False)]

        commentFormat = QtGui.QTextCharFormat()
        commentFormat.setFontItalic(True)
        commentFormat.setForeground(QtCore.Qt.darkGreen)
        self.rules += [(r"#[^\n]*", commentFormat, -1, -1, False)]

        literalFormat = QtGui.QTextCharFormat()
        literalFormat.setForeground(QtGui.QColor(65, 105, 225)) #royalblue
        self.rules += [
            # Whole docstring
            (r"'''.*'''", literalFormat, -1, -1, True),
            (r'""".*"""', literalFormat, -1, -1, True),
            # Hanging docstring (single quote)
            (r"'''.*$", literalFormat, -1, 2, False),
            (r"^.*'''", literalFormat, 2, -1, True),
            (r"^.*$", literalFormat, 2, 2, False),
            # Hanging docstring (double quote)
            (r'""".*$', literalFormat, -1, 3, False),
            (r'^.*"""', literalFormat, 3, -1, True),
            (r'^.*$', literalFormat, 3, 3, False),
            # Whole string
            (r"'[^']*'", literalFormat, -1, -1, False),
            (r'"[^"]*"', literalFormat, -1, -1, False),
            # Hanging string (single quote)
            (r"'[^']*$", literalFormat, -1,  0, False),
            (r"^[^']*$", literalFormat,  0,  0, False),
            (r"^[^']*'", literalFormat,  0, -1, False),
            # Hanging string (double quotes)
            (r'"[^"]*$', literalFormat, -1,  1, False),
            (r'^[^"]*$', literalFormat,  1,  1, False),
            (r'^[^"]*"', literalFormat,  1, -1, False),
            ]
        
    def highlightBlock(self, text):
        baseFormat = self.format(0)
        prevState = self.previousBlockState()
        self.setCurrentBlockState(prevState)        
        shift = 0
        while True:
            matchedRule = (None, -1, -1, -1, -1)
            for rule in self.rules:
                if rule[2]==self.currentBlockState():
                    RE = QtCore.QRegExp(rule[0])
                    RE.setMinimal(rule[4])
                    pos = RE.indexIn(text, shift)
                    if (pos!=-1 and (matchedRule[0]==None or pos<matchedRule[1]) and
                        RE.matchedLength()>0):
                        matchedRule = (rule[1], pos, RE.matchedLength(), rule[3])
            if matchedRule[0]!=None:
                self.setFormat(matchedRule[1], matchedRule[2], matchedRule[0])
                self.setCurrentBlockState(matchedRule[3])
                shift = matchedRule[1]+matchedRule[2]
            else:
                break

class PythonEditor(QtGui.QTextEdit):

    def __init__(self, parent=None):
        QtGui.QTextEdit.__init__(self, parent)
        if system.systemType=='Linux':
            self.defaultFontFamily = 'Monospace'
        else:
            self.defaultFontFamily = 'Courier'
        self.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        self.formatChanged(None)
        self.setCursorWidth(8)
        self.highlighter = PythonHighlighter(self.document())
        self.connect(self,
                     QtCore.SIGNAL('currentCharFormatChanged(QTextCharFormat)'),
                     self.formatChanged)

    def formatChanged(self, f):
        self.setFontFamily(self.defaultFontFamily)
        self.setFontPointSize(10.0)

    def keyPressEvent(self, event):
        """ keyPressEvent(event: QKeyEvent) -> Nont
        Handle tab with 4 spaces
        
        """
        if event.key()==QtCore.Qt.Key_Tab:
            self.insertPlainText('    ')
        else:
            # super(PythonEditor, self).keyPressEvent(event)
            QtGui.QTextEdit.keyPressEvent(self, event)
                 
class PythonSourceConfigurationWidget(PortTableConfigurationWidget):

    def __init__(self, module, controller, parent=None):
        PortTableConfigurationWidget.__init__(self, module, controller, parent)

    def doLayout(self):
        self.setWindowTitle('PythonSource Configuration')
        self.setLayout(QtGui.QVBoxLayout())
        self.layout().setMargin(0)
        self.layout().setSpacing(0)
        self.createPortTable()
        self.createEditor()
        self.createButtons()        


    def createPortTable(self):
        self.inputPortTable = PortTable(self)
        labels = QtCore.QStringList() << "Input Port Name" << "Type"
        self.inputPortTable.setHorizontalHeaderLabels(labels)
        self.outputPortTable = PortTable(self)
        labels = QtCore.QStringList() << "Output Port Name" << "Type"
        self.outputPortTable.setHorizontalHeaderLabels(labels)
        self.inputPortTable.initializePorts(self.module.input_port_specs)
        self.outputPortTable.initializePorts(self.module.output_port_specs, 
                                             True)
        self.layout().addWidget(self.inputPortTable)
        self.layout().addWidget(self.outputPortTable)
        self.performPortConnection(self.connect)
        self.inputPortTable.fixGeometry()
        self.outputPortTable.fixGeometry()

    def findSourceFunction(self):
        fid = -1
        for i in xrange(self.module.getNumFunctions()):
            if self.module.functions[i].name=='source':
                fid = i
                break
        return fid

    def createEditor(self):
        self.codeEditor = PythonEditor(self)
        fid = self.findSourceFunction()
        if fid!=-1:
            f = self.module.functions[fid]
            self.codeEditor.setPlainText(urllib.unquote(f.params[0].strValue))
        self.codeEditor.document().setModified(False)
        self.layout().addWidget(self.codeEditor, 1)
        
        self.cursorLabel = QtGui.QLabel()
        self.layout().addWidget(self.cursorLabel)
        self.connect(self.codeEditor, QtCore.SIGNAL('cursorPositionChanged()'),
                     self.updateCursorLabel)
        self.updateCursorLabel()

    def updateCursorLabel(self):
        cursor = self.codeEditor.textCursor()
        self.cursorLabel.setText('Line: %d / Col: %d' % (cursor.blockNumber()+1,
                                                            cursor.columnNumber()+1))

    def sizeHint(self):
        return QtCore.QSize(512, 512)

    def performPortConnection(self, operation):
        operation(self.inputPortTable.horizontalHeader(),
                  QtCore.SIGNAL('sectionResized(int,int,int)'),
                  self.portTableResize)
        operation(self.outputPortTable.horizontalHeader(),
                  QtCore.SIGNAL('sectionResized(int,int,int)'),
                  self.portTableResize)

    def portTableResize(self, logicalIndex, oldSize, newSize):
        self.performPortConnection(self.disconnect)
        if self.inputPortTable.horizontalHeader().sectionSize(logicalIndex)!=newSize:
            self.inputPortTable.horizontalHeader().resizeSection(logicalIndex,newSize)
        if self.outputPortTable.horizontalHeader().sectionSize(logicalIndex)!=newSize:
            self.outputPortTable.horizontalHeader().resizeSection(logicalIndex,newSize)
        self.performPortConnection(self.connect)

#     def newInputOutputPorts(self):
#         ports = []
#         for i in xrange(self.inputPortTable.rowCount()):
#             model = self.inputPortTable.model()
#             name = str(model.data(model.index(i, 0), QtCore.Qt.DisplayRole).toString())
#             sigstring = str(model.data(model.index(i,1), QtCore.Qt.UserRole).toString())
#             print sigstring
#             # typeName = str(model.data(model.index(i, 1), QtCore.Qt.DisplayRole).toString())
#             if name != '' and sigstring != '':
#                 print 'input', name, sigstring
#                 ports.append(('input', name, '(' + sigstring + ')'))
#         for i in xrange(self.outputPortTable.rowCount()):
#             model = self.outputPortTable.model()
#             name = str(model.data(model.index(i, 0), QtCore.Qt.DisplayRole).toString())
#             sigstring = str(model.data(model.index(i,1), QtCore.Qt.UserRole).toString())
#             print sigstring
#             # typeName = str(model.data(model.index(i, 1), QtCore.Qt.DisplayRole).toString())
#             if name!='' and sigstring != '':
#                 print 'output', name, sigstring
#                 ports.append(('output', name, '(' + sigstring + ')'))
#         return ports

#     def specsFromPorts(self, portType, ports):
#         return [(portType,
#                  p.name,
#                  '('+registry.get_descriptor(p.spec.signature[0][0]).name+')')
#                 for p in ports[0][1]]

#     def registryChanges(self, oldRegistry, newPorts):
#         if oldRegistry:
#             oldIn = self.specsFromPorts('input',
#                                         oldRegistry.all_destination_ports(self.module_descriptor))
#             oldOut = self.specsFromPorts('output',
#                                          oldRegistry.all_source_ports(self.module_descriptor))
#         else:
#             oldIn = []
#             oldOut = []
#         deletePorts = [p for p in oldIn if not p in newPorts]
#         deletePorts += [p for p in oldOut if not p in newPorts]
#         addPorts = [p for p in newPorts if ((not p in oldIn) and (not p in oldOut))]
#         return (deletePorts, addPorts)

    def updateVistrail(self):
        """updateVistrail() -> None
        Update vistrail to contain changes to the python source

        """
        (deleted_ports, added_ports) = \
            self.getPortDiff('input', self.inputPortTable)
        (output_deleted_ports, output_added_ports) = \
            self.getPortDiff('output', self.outputPortTable)
        deleted_ports.extend(output_deleted_ports)
        added_ports.extend(output_added_ports)

        functions = []
        if self.codeEditor.document().isModified():
            code = urllib.quote(str(self.codeEditor.toPlainText()))
            functions.append(('source', [code]))
        if len(deleted_ports) + len(added_ports) + len(functions) == 0:
            # nothing changed
            return
        try:
            self.controller.update_ports_and_functions(self.module.id, 
                                                       deleted_ports, 
                                                       added_ports,
                                                       functions)
        except PortAlreadyExists, e:
            QtGui.QMessageBox.critical(self, 'Port Already Exists', str(e))
            return False
        return True

#     def updateActionsHandler(self, controller):
#         oldRegistry = self.module.registry
#         newPorts = self.newInputOutputPorts()
#         (deletePorts, addPorts) = self.registryChanges(oldRegistry, newPorts)
#         for (cid, c) in controller.current_pipeline.connections.items():
#             if ((c.sourceId==self.module.id and
#                  any(c.source.name==p[1] for p in deletePorts)) or
#                 (c.destinationId==self.module.id and
#                  any(c.destination.name==p[1] for p in deletePorts))):
#                 controller.delete_connection(cid)
#         for p in deletePorts:
#             controller.delete_module_port(self.module.id, p)
#         for p in addPorts:
#             controller.add_module_port(self.module.id, p)
#         if self.codeEditor.document().isModified():
#             code = urllib.quote(str(self.codeEditor.toPlainText()))
#             fid = self.findSourceFunction()
            
#             # FIXME make sure that this makes sense
#             if fid==-1:
#                 # do add function
#                 fid = self.module.getNumFunctions()
#                 f = ModuleFunction(pos=fid,
#                                    name='source')
#                 param = ModuleParam(type='String',
#                                     val=code,
#                                     alias='',
#                                     name='<no description>',
#                                     pos=0)
#                 f.addParameter(param)
#                 controller.add_method(self.module.id, f)
#             else:
#                 # do change parameter
#                 paramList = [(code, 'String', None, 
#                               'edu.utah.sci.vistrails.basic', '')]
#                 controller.replace_method(self.module, fid, paramList)
#             action = ChangeParameterAction()
#             action.addParameter(self.module.id, fid, 0, 'source',
#                                 '<no description>',code,'String', '')
#             controller.performAction(action)
                
#     def okTriggered(self, checked = False):
#         self.updateActionsHandler(self.controller)
#         self.emit(QtCore.SIGNAL('doneConfigure()'))
#         self.close()
