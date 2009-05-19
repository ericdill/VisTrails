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
""" This file specifies the configuration widget for Tuple
module. This should be used as a template for creating a configuration
for other modules. The widget here should inherit from
core.modules.module_configure.StandardModuleConfigurationWidget, which
is also a QWidget.

"""
from PyQt4 import QtCore, QtGui
from core.modules.module_configure import StandardModuleConfigurationWidget
from core.modules.module_registry import get_module_registry
from core.utils import PortAlreadyExists

############################################################################

class PortTable(QtGui.QTableWidget):
    def __init__(self, parent=None):
        QtGui.QTableWidget.__init__(self,1,2,parent)
        self.horizontalHeader().setResizeMode(QtGui.QHeaderView.Interactive)
        self.horizontalHeader().setMovable(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.delegate = PortTableItemDelegate(self)
        self.setItemDelegate(self.delegate)
        self.setFrameStyle(QtGui.QFrame.NoFrame)
        self.connect(self.model(),
                     QtCore.SIGNAL('dataChanged(QModelIndex,QModelIndex)'),
                     self.handleDataChanged)

    def sizeHint(self):
        return QtCore.QSize()

    def fixGeometry(self):
        rect = self.visualRect(self.model().index(self.rowCount()-1,
                                                  self.columnCount()-1))
        self.setFixedHeight(self.horizontalHeader().height()+
                            rect.y()+rect.height()+1)

    def handleDataChanged(self, topLeft, bottomRight):
        if topLeft.column()==0:
            text = str(self.model().data(topLeft, QtCore.Qt.DisplayRole).toString())
            changedGeometry = False
            if text!='' and topLeft.row()==self.rowCount()-1:
                self.setRowCount(self.rowCount()+1)
                changedGeometry = True
            if text=='' and topLeft.row()<self.rowCount()-1:
                self.removeRow(topLeft.row())
                changedGeometry = True
            if changedGeometry:
                self.fixGeometry()

    def initializePorts(self, port_specs, reverse_order=False):
        self.disconnect(self.model(),
                        QtCore.SIGNAL('dataChanged(QModelIndex,QModelIndex)'),
                        self.handleDataChanged)
        if reverse_order:
            port_specs_iter = reversed(port_specs)
        else:
            port_specs_iter = port_specs
        for p in port_specs_iter:
            model = self.model()
            sigstring = p.sigstring[1:-1]
            siglist = sigstring.split(':')
            short_name = "%s (%s)" % (siglist[1], siglist[0])
            model.setData(model.index(self.rowCount()-1, 1),
                          QtCore.QVariant(sigstring),
                          QtCore.Qt.UserRole)
            model.setData(model.index(self.rowCount()-1, 1),
                          QtCore.QVariant(short_name),
                          QtCore.Qt.DisplayRole)
            model.setData(model.index(self.rowCount()-1, 0),
                          QtCore.QVariant(p.name),
                          QtCore.Qt.DisplayRole)
            self.setRowCount(self.rowCount()+1)
        self.connect(self.model(),
                     QtCore.SIGNAL('dataChanged(QModelIndex,QModelIndex)'),
                     self.handleDataChanged)
            
    def getPorts(self):
        ports = []
        for i in xrange(self.rowCount()):
            model = self.model()
            name = str(model.data(model.index(i, 0), 
                                  QtCore.Qt.DisplayRole).toString())
            sigstring = str(model.data(model.index(i, 1), 
                                       QtCore.Qt.UserRole).toString())
            if name != '' and sigstring != '':
                ports.append((name, '(' + sigstring + ')', i))
        return ports

class PortTableItemDelegate(QtGui.QItemDelegate):

    def createEditor(self, parent, option, index):
        registry = get_module_registry()
        if index.column()==1: #Port type
            combo = QtGui.QComboBox(parent)
            combo.setEditable(False)
            # FIXME just use descriptors here!!
            for _, pkg in sorted(registry.packages.iteritems()):
                for _, descriptor in sorted(pkg.descriptors.iteritems()):
                    combo.addItem("%s (%s)" % (descriptor.name, 
                                               descriptor.identifier),
                                  QtCore.QVariant(descriptor.sigstring))
            return combo
        else:
            return QtGui.QItemDelegate.createEditor(self, parent, option, index)

    def setEditorData(self, editor, index):
        if index.column()==1:
            data = index.model().data(index, QtCore.Qt.UserRole)
            editor.setCurrentIndex(editor.findData(data))
        else:
            QtGui.QItemDelegate.setEditorData(self, editor, index)

    def setModelData(self, editor, model, index):
        if index.column()==1:
            model.setData(index, editor.itemData(editor.currentIndex()), 
                          QtCore.Qt.UserRole)
            model.setData(index, QtCore.QVariant(editor.currentText()), 
                          QtCore.Qt.DisplayRole)
        else:
            QtGui.QItemDelegate.setModelData(self, editor, model, index)

############################################################################

class PortTableConfigurationWidget(StandardModuleConfigurationWidget):
    """
    PortTableConfigurationWidget is the configuration widget for a
    tuple-like module, we want to build an interface for specifying a
    number of input (output) ports and the type of each port. Then
    compose (decompose) a tuple of those input as a result.

    When subclassing StandardModuleConfigurationWidget, there are
    only two things we need to care about:
    
    1) The builder will provide the VistrailController (through the
       constructor) associated with the pipeline the module is in. The
       configuration widget can use the controller to change the
       current vistrail such as delete connections, add/delete module
       port...

    2) The builder also provide the current Module object (through the
       constructor) of the module. This is the instance of the module
       in the pipeline. Changes to this Module object usually will not
       result a new version in the current Vistrail. Such changes are
       change the visibility of input/output ports on the builder,
       change module color.

       Each module has a local set of input and output ports that may
       change, unlike those stored by the global registry. The same
       module can have different types of input ports at two different
       time in the same vistrail.

    That's it, the rest of the widget will be just like a regular Qt
    widget.
    
    """
    def __init__(self, module, controller, parent=None):
        """ PortTableConfigurationWidget(module: Module,
                                         controller: VistrailController,
                                         parent: QWidget)
                                         -> PortTableConfigurationWidget                                       
        Let StandardModuleConfigurationWidget constructor store the
        controller/module object from the builder and set up the
        configuration widget.        
        After StandardModuleConfigurationWidget constructor, all of
        these will be available:
        self.module : the Module object int the pipeline        
        self.module_descriptor: the descriptor for the type registered in the registry,
                          i.e. Tuple
        self.controller: the current vistrail controller
                                       
        """
        StandardModuleConfigurationWidget.__init__(self, module,
                                                   controller, parent)
        self.doLayout()

    def doLayout(self):
        raise VistrailsInternalError("Must implement doLayout in subclass")

    def updateVistrail(self):
        msg = "Must implement updateVistrail in subclass"
        raise VistrailsInternalError(msg)

    def createButtons(self):
        """ createButtons() -> None
        Create and connect signals to Ok & Cancel button
        
        """
        self.buttonLayout = QtGui.QHBoxLayout()
        self.buttonLayout.setMargin(5)
        self.okButton = QtGui.QPushButton('&OK', self)
        self.okButton.setAutoDefault(False)
        self.okButton.setFixedWidth(100)
        self.buttonLayout.addWidget(self.okButton)
        self.cancelButton = QtGui.QPushButton('&Cancel', self)
        self.cancelButton.setAutoDefault(False)
        self.cancelButton.setShortcut('Esc')
        self.cancelButton.setFixedWidth(100)
        self.buttonLayout.addWidget(self.cancelButton)
        self.layout().addLayout(self.buttonLayout)
        self.connect(self.okButton, QtCore.SIGNAL('clicked(bool)'),
                     self.okTriggered)
        self.connect(self.cancelButton, QtCore.SIGNAL('clicked(bool)'),
                     self.close)        

    def sizeHint(self):
        """ sizeHint() -> QSize
        Return the recommended size of the configuration window
        
        """
        return QtCore.QSize(512, 256)

    def okTriggered(self, checked = False):
        """ okTriggered(checked: bool) -> None
        Update vistrail controller and module when the user click Ok
        
        """
        if self.updateVistrail():
            self.emit(QtCore.SIGNAL('doneConfigure()'))
            self.close()

    def getRegistryPorts(self, registry, type):
        if not registry:
            return []
        if type == 'input':
            getter = registry.destination_ports_from_descriptor
        elif type == 'output':
            getter = registry.source_ports_from_descriptor
        else:
            raise VistrailsInternalError("Unrecognized port type '%s'", type)
        return [(p.name, p.sigstring) for p in getter(self.module_descriptor)]
        
    def registryChanges(self, old_ports, new_ports):
        deleted_ports = [p for p in old_ports if p not in new_ports]
        added_ports = [p for p in new_ports if p not in old_ports]
        return (deleted_ports, added_ports)
    
    def getPortDiff(self, p_type, port_table):
        if p_type == 'input':
            old_ports = [(p.name, p.sigstring, p.sort_key)
                         for p in self.module.input_port_specs]
        elif p_type == 'output':
            old_ports = [(p.name, p.sigstring, p.sort_key) 
                         for p in self.module.output_port_specs]
        else:
            old_ports = []
        # old_ports = self.getRegistryPorts(self.module.registry, p_type)
        new_ports = port_table.getPorts()
        (deleted_ports, added_ports) = \
            self.registryChanges(old_ports, new_ports)
        deleted_ports = [(p_type,) + p for p in deleted_ports]
        added_ports = [(p_type,) + p for p in added_ports]
        return (deleted_ports, added_ports)

    
class TupleConfigurationWidget(PortTableConfigurationWidget):
    def __init__(self, module, controller, parent=None):
        """ TupleConfigurationWidget(module: Module,
                                     controller: VistrailController,
                                     parent: QWidget)
                                     -> TupleConfigurationWidget

        Let StandardModuleConfigurationWidget constructor store the
        controller/module object from the builder and set up the
        configuration widget.        
        After StandardModuleConfigurationWidget constructor, all of
        these will be available:
        self.module : the Module object int the pipeline        
        self.module_descriptor: the descriptor for the type registered in 
           the registry, i.e. Tuple
        self.controller: the current vistrail controller
                                       
        """
        PortTableConfigurationWidget.__init__(self, module,
                                              controller, parent)


    def doLayout(self):
        # Give it a nice window title
        self.setWindowTitle('Tuple Configuration')

        # Add an empty vertical layout
        centralLayout = QtGui.QVBoxLayout()
        centralLayout.setMargin(0)
        centralLayout.setSpacing(0)
        self.setLayout(centralLayout)
        
        # Then add a PortTable to our configuration widget
        self.portTable = PortTable(self)
        self.portTable.setHorizontalHeaderLabels(
            QtCore.QStringList() << 'Input Port Name' << 'Type')
        
        # We know that the Tuple module initially doesn't have any
        # input port, we just use the local registry to see what ports
        # it has at the time of configuration.
        self.portTable.initializePorts(self.module.input_port_specs)
        self.portTable.fixGeometry()
        centralLayout.addWidget(self.portTable)

        # We need a padded widget to take all vertical white space away
        paddedWidget = QtGui.QWidget(self)
        paddedWidget.setSizePolicy(QtGui.QSizePolicy.Ignored,
                                   QtGui.QSizePolicy.Expanding)
        centralLayout.addWidget(paddedWidget, 1)

        # Then we definitely need an Ok & Cancel button
        self.createButtons()

    def updateVistrail(self):
        """ updateVistrail() -> None
        Update Vistrail to contain changes in the port table
        
        """
        (deleted_ports, added_ports) = self.getPortDiff('input', self.portTable)
        if len(deleted_ports) + len(added_ports) == 0:
            # nothing changed
            return
        current_ports = self.portTable.getPorts()
        # note that the sigstring and sort_key for deletion doesn't matter
        deleted_ports.append(('output', 'value'))
        if len(current_ports) > 0:
            spec = "(" + ','.join(p[1][1:-1] for p in current_ports) + ")"
            added_ports.append(('output', 'value', spec, -1))
        try:
            self.controller.update_ports(self.module.id, deleted_ports, 
                                         added_ports)
        except PortAlreadyExists, e:
            QtGui.QMessageBox.critical(self, 'Port Already Exists', str(e))
            return False
        return True            

class UntupleConfigurationWidget(PortTableConfigurationWidget):
    def __init__(self, module, controller, parent=None):
        """ UntupleConfigurationWidget(module: Module,
                                     controller: VistrailController,
                                     parent: QWidget)
                                     -> UntupleConfigurationWidget                                       
        Let StandardModuleConfigurationWidget constructor store the
        controller/module object from the builder and set up the
        configuration widget.        
        After StandardModuleConfigurationWidget constructor, all of
        these will be available:
        self.module : the Module object int the pipeline        
        self.module_descriptor: the descriptor for the type registered in the registry,
                          i.e. Tuple
        self.controller: the current vistrail controller
                                       
        """
        PortTableConfigurationWidget.__init__(self, module,
                                              controller, parent)


    def doLayout(self):
        # Give it a nice window title
        self.setWindowTitle('Untuple Configuration')

        # Add an empty vertical layout
        centralLayout = QtGui.QVBoxLayout()
        centralLayout.setMargin(0)
        centralLayout.setSpacing(0)
        self.setLayout(centralLayout)
        
        # Then add a PortTable to our configuration widget
        self.portTable = PortTable(self)
        self.portTable.setHorizontalHeaderLabels(
            QtCore.QStringList() << 'Output Port Name' << 'Type')
        
        # We know that the Tuple module initially doesn't have any
        # input port, we just use the local registry to see what ports
        # it has at the time of configuration.
        self.portTable.initializePorts(self.module.output_port_specs, True)
        self.portTable.fixGeometry()
        centralLayout.addWidget(self.portTable)

        # We need a padded widget to take all vertical white space away
        paddedWidget = QtGui.QWidget(self)
        paddedWidget.setSizePolicy(QtGui.QSizePolicy.Ignored,
                                   QtGui.QSizePolicy.Expanding)
        centralLayout.addWidget(paddedWidget, 1)

        # Then we definitely need an Ok & Cancel button
        self.createButtons()

    def updateVistrail(self):
        """ updateVistrail() -> None
        Update Vistrail to contain changes in the port table
        
        """

        (deleted_ports, added_ports) = self.getPortDiff('output', 
                                                        self.portTable)
        if len(deleted_ports) + len(added_ports) == 0:
            # nothing changed
            return
        current_ports = self.portTable.getPorts()
        # note that the sigstring for deletion doesn't matter
        deleted_ports.append(('input', 'value'))
        if len(current_ports) > 0:
            spec = "(" + ','.join(p[1][1:-1] for p in current_ports) + ")"
            added_ports.append(('input', 'value', spec, -1))
        try:
            self.controller.update_ports(self.module.id, deleted_ports, 
                                         added_ports)
        except PortAlreadyExists, e:
            QtGui.QMessageBox.critical(self, 'Port Already Exists', str(e))
            return False
        return True
