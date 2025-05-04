import xml.etree.ElementTree as ET
import json, os

#parsing test_input.xml
class Parser:
    def __init__(self, input_file):
        self.input_file = input_file 
        self.classes = {}  #dict to store class information
        self.aggregations = []  #storing aggregation relationships
        self.parsing()

    def parsing(self):
        #parsing test_input.xml to get root element
        tree = ET.parse(self.input_file)
        root = tree.getroot()

        #finding adll class elements in .xml
        for elem in root.findall('Class'):
            class_name = elem.get('name')
            is_root = elem.get('isRoot') == 'true'
            documentation = elem.get('documentation', '')
            
            #collecting attributes
            attributes = []
            for attr in elem.findall('Attribute'):
                attributes.append({
                    'name': attr.get('name'),
                    'type': attr.get('type')
                })
            
            #storing information in classes dict
            self.classes[class_name] = {
                'isRoot': is_root,
                'documentation': documentation,
                'attributes': attributes,
                'children': []
            }

        #finding all aggregation elements in .xml
        for agg in root.findall('Aggregation'):
            source = agg.get('source')
            target = agg.get('target')
            source_multiplicity = agg.get('sourceMultiplicity')
            target_multiplicity = agg.get('targetMultiplicity')
            
            #storing previous info
            self.aggregations.append({
                'source': source,
                'target': target,
                'sourceMultiplicity': source_multiplicity,
                'targetMultiplicity': target_multiplicity
            })
            
            #appends classes, if they exist
            if target in self.classes:
                self.classes[target]['children'].append({
                    'name': source,
                    'min': source_multiplicity.split('..')[0],
                    'max': source_multiplicity.split('..')[-1]
                })


class MetaJsonGenerator:
    def __init__(self, classes, aggregations):
        self.classes = classes
        self.aggregations = aggregations
    
    #generating new meta.json
    def generate(self): 
        meta_data = []
        
        #process of each class in the classes dict
        for class_name, class_info in self.classes.items():
            parameters = []
            
            #adds all children as parameters
            for attr in class_info['attributes']:
                parameters.append({
                    'name': attr['name'],
                    'type': attr['type']
                })
            
            #adds all children as parameters with type 'class'
            for child in class_info['children']:
                parameters.append({
                    'name': child['name'],
                    'type': 'class'
                })
            
            #finds multiplicity from aggregations where class is source
            min_val = "1"
            max_val = "1"
            for agg in self.aggregations:
                if agg['source'] == class_name:
                    parts = agg['sourceMultiplicity'].split('..')
                    min_val = parts[0]
                    max_val = parts[-1]
                    break
            
            #adds class meta to list
            meta_data.append({
                'class': class_name,
                'documentation': class_info['documentation'],
                'isRoot': class_info['isRoot'],
                'min': min_val,
                'max': max_val,
                'parameters': parameters
            })
        
        return meta_data


class ConfigXmlGenerator:
    def __init__(self, classes):
        self.classes = classes
    
    #generating new config.xml
    def generate(self):
        root_class = next((name for name, info in self.classes.items() if info['isRoot']), None)
        if not root_class:
            return "<error>No root class found</error>"
        
        #using recursive function to build XML for class and its' children
        def build_xml(class_name, indent=1):
            class_info = self.classes[class_name]
            spaces = '    ' * indent
            xml_lines = []
            
            #adds opening tag to class
            xml_lines.append(f"{spaces}<{class_name}>")
            
            #adds all attributes as child elems and then recursively adds all child classes
            for attr in class_info['attributes']:
                xml_lines.append(f"{spaces}    <{attr['name']}>{attr['type']}</{attr['name']}>")
            
            for child in class_info['children']:
                child_class = child['name']
                if child_class in self.classes:
                    xml_lines.append(build_xml(child_class, indent + 1))
            
            #adds closing tag
            xml_lines.append(f"{spaces}</{class_name}>")
            
            return '\n'.join(xml_lines)
        
        xml_content = build_xml(root_class, 0)
        return f'<?xml version="1.0" ?>\n{xml_content}'


def main():
    base_dir = 'C:/Users/Nikita Morozov/vscode' #change if different
    out_dir = os.path.join(base_dir, 'out') #creating and output directory
    os.makedirs(out_dir, exist_ok=True)

    input_file = os.path.join(base_dir, 'test_input.xml')
    parser = Parser(input_file)
    
    #generating meta.json
    meta_generator = MetaJsonGenerator(parser.classes, parser.aggregations)
    meta_data = meta_generator.generate()
    meta_output = os.path.join(out_dir, 'meta.json')
    with open(meta_output, 'w') as f:
        json.dump(meta_data, f, indent=4)
    
    #generating config.xml
    config_generator = ConfigXmlGenerator(parser.classes)
    config_xml = config_generator.generate()
    config_output = os.path.join(out_dir, 'config.xml')
    with open(config_output, 'w') as f:
        f.write(config_xml)

    print('successesfully created in /out')

if __name__ == "__main__":
    main()
