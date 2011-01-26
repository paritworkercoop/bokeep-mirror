# Copyright (C)  2008 ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
#
# This file is part of Bo-Keep.
#
# Bo-Keep is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Mark Jenkins <mark@parit.ca>

from xml.sax.saxutils import XMLGenerator
from xml.sax.xmlreader import AttributesNSImpl

from itertools import ifilter

ELEMENT_NAME, ELEMENT_ATTRIBUTES, REQUIRED_SUB_ELEMENT_CLASSES, \
OPTIONAL_SUB_ELEMENT_CLASSES, ELEMENT_PARENTS, ELEMENT_DATA_FIELDS, \
AUTOMATIC_SUB_ELEMENT_CLASSES = range(7)

NEW_VISIBLE_CLASS, OPTIONAL_AUTOMATIC = range(2)

def find_class_instance_is_of(instance, class_list):
    for test_class in class_list:
        if isinstance(instance, test_class):
            return test_class
    return None

class AttributeSpec(object):
    def __init__(self, attr_name, mandatory=False,
                 default=None, init_arg_name=None, prefix=None, uri=None):
        if init_arg_name is None:
            init_arg_name = attr_name
        self.init_arg_name = init_arg_name
        self.mandatory = mandatory
        self.default = default
        self.uri = uri
        self.prefix = prefix
        self.attribute_key = (self.uri, attr_name)
        if prefix is None:
            self.attribute_qname = attr_name
        else:
            self.attribute_qname = "%s:%s" % (self.prefix, attr_name)


class XMLElement(object):
    specs = ()

    whitespace_after_start_tag = "\n"
    whitespace_after_end_tag = "\n"

    def __init__(self, sub_elements=(), **kargs):
        self.init_args = kargs
        self.sub_elements = sub_elements
        for init_arg_name in self.init_args:
            self.init_args[init_arg_name] = str(self.init_args[init_arg_name])

    @classmethod
    def automatic_creation_requirements_satisfyed(cls, init_args):
        return True

    def check_parent_against_spec(self, parent):
        # If the element doesn't have a parent, it better not specify any
        if parent is None:
            if len(self.specs[ELEMENT_PARENTS]) is not 0:
                raise Exception(
                    "%s instance has no parent element, but should" %
                    self.__class__.__name__ )        
        # else the parent should be an instance of one of the posible
        # parrent classes
        else:
            for parrent_class in self.specs[ELEMENT_PARENTS]:
                if isinstance(parent, parrent_class):
                    break
            else:
                raise Exception("%s doesn't have a valid parent element" %
                                self.__class__.__name__)

    def ensure_init_arg_is_in_place(self, attribute_spec):
        init_arg_name = attribute_spec.init_arg_name 
        # if the initailization argument from specification wasn't
        # found, see if a default is availible
        if init_arg_name not in self.init_args and \
           attribute_spec.default is not None:    
            self.init_args[init_arg_name] = attribute_spec.default

            # we can't move on if the attribute is undefined, has
            # no default, but is mandatory
            if attribute_spec.mandatory and attribute_spec.default is None:
                raise Exception("the attribute %s for element %s is "
                                "mandatory, but was not defined and no "
                                "default was specified either" % 
                                (attribute_spec.attribute_key,
                                 self.specs[ELEMENT_NAME] )
                                    ) # end Exception()
    
    def generate_xml_start_tag_with_attributes(
        self, xml_out, ns_prefixes, ns_prefixes_local):
        attribute_value_dict = {}
        attribute_qname_dict = {}        

        attribute_specs = self.specs[ELEMENT_ATTRIBUTES]
        # go through the attribute specifications and use values from
        # to set attributes of this element
        for attribute_spec in attribute_specs:
            prefix = attribute_spec.prefix
            if prefix is not None and prefix not in ns_prefixes:
                ns_prefixes.add( prefix )
                ns_prefixes_local.add( prefix )
                xml_out.startPrefixMapping( prefix, attribute_spec.uri )

            self.ensure_init_arg_is_in_place(attribute_spec)

            init_arg_name = attribute_spec.init_arg_name 
            # if the initailization argument from specification exists
            # use it in the current elements attributes
            if init_arg_name in self.init_args:
                attribute_value_dict[attribute_spec.attribute_key] = \
                    self.init_args[init_arg_name]
                attribute_qname_dict[attribute_spec.attribute_key] = \
                    attribute_spec.attribute_qname


        # start the element, use the name from the specification, and
        # set the attributes as disovered above
        xml_out.startElementNS(
            (None, self.specs[ELEMENT_NAME]), self.specs[ELEMENT_NAME],
            AttributesNSImpl( attribute_value_dict, attribute_qname_dict )
            )
        xml_out.ignorableWhitespace(self.whitespace_after_start_tag)

    def generate_xml_data(self, xml_out):
        # output the element's data, if availible
        for element_data_attribute_spec in self.specs[ELEMENT_DATA_FIELDS]:
            self.ensure_init_arg_is_in_place(element_data_attribute_spec)
            init_arg_name = element_data_attribute_spec.init_arg_name 
            if init_arg_name in self.init_args:
                xml_out.characters(self.init_args[init_arg_name])

    def generate_xml_sub_elements(self, xml_out, ns_prefixes):
        # go through the sub element instances, check the spec to see if
        # they're instances of one of the allowed elements, track
        # which required elements have been utilized, and 
        #
        # build a set of the required elements, remove them as we
        # find they are used
        required_sub_element_class_set = set(
            self.specs[REQUIRED_SUB_ELEMENT_CLASSES] )

        def handle_new_automatic_sub_element(element_class):
            required_sub_element_class_set.add(element_class)
            return element_class()
        new_sub_elements = [
            handle_new_automatic_sub_element(element_class)
            for element_class in self.specs[AUTOMATIC_SUB_ELEMENT_CLASSES] ]

        new_sub_elements.extend( self.sub_elements )
        self.sub_elements = new_sub_elements
        
        for sub_element in self.sub_elements:
            match_class = find_class_instance_is_of(
                sub_element,
                required_sub_element_class_set)
            # the below looks like a more correct value to use as a
            # second argument above, 
            # (to allow multiple instances of the required sub element),
            # but it isn't working
            #self.specs[REQUIRED_SUB_ELEMENT_CLASSES] )
            
            if match_class is not None:
                if sub_element.__class__ in required_sub_element_class_set:
                    required_sub_element_class_set.remove(
                        sub_element.__class__)
            else:
                match_class = find_class_instance_is_of(
                    sub_element, self.specs[OPTIONAL_SUB_ELEMENT_CLASSES])
                if match_class is None:
                    raise Exception(
                        "%s is not a valid sub element of any posible " \
                        "sub elements" % sub_element.__class__.__name__ )
                
            # recursivly create the sub element
            sub_element.generate_xml(xml_out, self, ns_prefixes)
            
        if len(required_sub_element_class_set) is not 0:
            raise Exception("one of the required sub elements of "
                            "%s was not found" % self.specs[ELEMENT_NAME] )
            
    def generate_xml_end_tag(self, xml_out):
        xml_out.endElementNS( (None, self.specs[ELEMENT_NAME]),
                              self.specs[ELEMENT_NAME] )        
        xml_out.ignorableWhitespace(self.whitespace_after_end_tag)
        
    def generate_xml(self, xml_out, parent=None, ns_prefixes=None):
        self.parent = parent
        self.check_parent_against_spec(parent)
        
        if ns_prefixes is None:
            ns_prefixes = set()
        ns_prefixes_local = set()

        self.generate_xml_start_tag_with_attributes(
            xml_out, ns_prefixes, ns_prefixes_local)

        self.generate_xml_data(xml_out)
        
        self.generate_xml_sub_elements(xml_out, ns_prefixes)

        self.generate_xml_end_tag(xml_out)
        
        for prefix in ns_prefixes_local:
            xml_out.endPrefixMapping(prefix)
            ns_prefixes.remove(prefix)

    @staticmethod
    def setup_element_class_specs(
        element_class,
        **kargs):
        
        kargs_with_empty_tuple_default = (
            "attribute_specs", "required_sub_element_classes",
            "optional_sub_element_classes", "element_parents",
            "element_data_fields", "automatic_sub_element_classes" )

        for arg in kargs_with_empty_tuple_default:
            if arg not in kargs:
                kargs[arg] = ()
        
        # if an element name hasn't been specified, assume it is the
        # same as the class name. (Very covienent!)
        if "element_name" not in kargs or kargs["element_name"] is None:
            kargs["element_name"] = element_class.__name__

        element_class.specs = (
            kargs["element_name"],           # ELEMENT_NAME
            kargs["attribute_specs"],        # ELEMENT_ATTRIBUTES
            kargs[
            "required_sub_element_classes"], # REQUIRED_SUB_ELEMENT_CLASSES
            kargs[
            "optional_sub_element_classes"], # OPTIONAL_SUB_ELEMENT_CLASSES
            kargs["element_parents"],        # ELEMENT_PARENTS
            kargs["element_data_fields"],    # ELEMENT_DATA_FIELDS
            kargs[
            "automatic_sub_element_classes"],# AUTOMATIC_SUB_ELEMENT_CLASSES
            )

    def return_nth_parent(self, level):
        if level is 0:
            return self
        else:
            return self.parent.return_nth_parent(level - 1)

class ParentScrapingXMLElement(XMLElement):
    parent_level = 1
    init_args_to_copy = ()
    whitespace_after_start_tag = ""
    whitespace_after_end_tag = "\n"
    mandatory = True

    @classmethod
    def automatic_creation_requirements_satisfyed(cls, init_args):
        if cls.mandatory:
            return True
        else:
            init_arg_set = set( init_args.iterkeys() )
            for init_arg in cls.init_args_to_copy:
                if init_arg in init_arg_set:
                    return True
            print 'could not find any of', cls.init_args_to_copy, \
                  'in', init_args
            
            return False
    
    def generate_xml(self, xml_out, parent, ns_prefixes):
        self.parent = parent
        parent_with_data = self.return_nth_parent( self.parent_level )
        all_args_copied = True
        for init_arg_to_copy in self.init_args_to_copy:
            if init_arg_to_copy in parent_with_data.init_args or \
               self.mandatory:
            
                self.init_args[init_arg_to_copy] = \
                parent_with_data.init_args[init_arg_to_copy]
            else:
                all_args_copied = False

        if all_args_copied:
            XMLElement.generate_xml(self, xml_out, parent, ns_prefixes)

    @staticmethod
    def setup_element_class_specs(
        element_class,
        element_data_fields,
        parent_level=1,
        **kargs ):
        
        element_class.parent_level = parent_level
        element_class.init_args_to_copy = [
            element_data_field.init_arg_name
            for element_data_field in element_data_fields
            ]

        kargs['element_data_fields'] = element_data_fields
        XMLElement.setup_element_class_specs(element_class, **kargs )
        
    @staticmethod
    def setup_simple_scraper_specs(
    element_class, attr_name, parent_class, parent_level=1, mandatory=True):

        element_class.setup_element_class_specs(
            element_class,
            element_data_fields=(
            AttributeSpec(attr_name, mandatory=mandatory), ),
            parent_level=parent_level,
            element_parents=(parent_class,),
            element_name=attr_name )
        element_class.mandatory = mandatory

def generate_XML_element_classes_from_shorthand(
    dict_to_add_to, element_shorthand_spec,
    super_class=None, super_class_sub_class_list=[],
    parent_level=0,
    mandatory=True ):
    
    if isinstance(element_shorthand_spec, list):
        class new_element_class(XMLElement):
            pass
        name_found = False
        attribute_specs = []
        automatic_sub_class_list = []
        for element_spec_peice in element_shorthand_spec:
            if isinstance(element_spec_peice, str) and not name_found:
                name_found = True
                new_element_class.__name__ = element_spec_peice
            elif element_spec_peice == NEW_VISIBLE_CLASS:
                dict_to_add_to[new_element_class.__name__] = new_element_class
            elif element_spec_peice == OPTIONAL_AUTOMATIC:
                mandatory = False
            elif isinstance(element_spec_peice, AttributeSpec):
                attribute_specs.append(element_spec_peice)
            elif isinstance(element_spec_peice, list) or \
                 isinstance(element_spec_peice, str) and name_found:
                generate_XML_element_classes_from_shorthand(
                    dict_to_add_to, element_spec_peice,
                    new_element_class, automatic_sub_class_list,
                    parent_level=parent_level+1, mandatory=mandatory )
                mandatory = True
        if super_class == None:
            element_parents_arg = ()
        else:
            element_parents_arg = (super_class,)
        
        new_element_class.setup_element_class_specs(
            new_element_class,
            attribute_specs=tuple(attribute_specs),
            element_parents=element_parents_arg,
            automatic_sub_element_classes=automatic_sub_class_list,
            parent_level=parent_level )
    else:
        assert( isinstance(element_shorthand_spec, str) )
        class new_element_class(ParentScrapingXMLElement):
            pass
        new_element_class.setup_simple_scraper_specs(
            new_element_class, element_shorthand_spec, super_class,
            parent_level, mandatory)
    super_class_sub_class_list.append( new_element_class )



def generate_xml(output_file, top_document_object, encoding='iso-8859-1'):
    xml_out = XMLGenerator(output_file, encoding)
    xml_out.startDocument()
    top_document_object.generate_xml(xml_out)
    xml_out.endDocument()

