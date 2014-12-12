#!/usr/bin/env python

#   Copyright (c) 2014 David Anthony
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import argparse
import os
import rosbag
import roslib
import sys
import subprocess
import yaml
roslib.load_manifest('rosbag')


def build_parser():
    """Creates parser for command line arguments """
    parser = argparse.ArgumentParser(description='Bag reader')
    parser.add_argument('-b', '--bag',
                        help='Bag file to read',
                        required=True,
                        type=str)
    parser.add_argument('-i', '--info',
                        help='List topics and fields within topics',
                        required=False,
                        action='store_true')
    parser.add_argument('-s', '--stats',
                        help='Display how many messages were published on each topic',
                        required=False,
                        action='store_true')
    parser.add_argument('-t', '--topic',
                        help='Topic to write to csv file',
                        required=False,
                        action='store',
                        type=str)
    parser.add_argument('-o', '--output_file',
                        help='Output file name',
                        required=False,
                        action='store',
                        dest='out_file',
                        type=str)

    return parser


def validate_args(cmd_args):
    """ Validates the arguments parsed by the parser generated in the build_parser() function. We
        must always have a bag file. There are two options for processing it. One is to just get the
        info (-i) and the other is to convert a topic in it to a csv file. For the second option,
        both the topic and output file must be specified
    """
    valid = cmd_args.bag is not None

    if not valid:
        print('Must specify a bag file')

    if valid:
        valid = os.path.isfile(cmd_args.bag)
        if not valid:
            print('Invalid bag file')

    if valid:
        valid = (cmd_args.info and
                 (cmd_args.topic is None and cmd_args.out_file is None) and
                 (not cmd_args.stats)) \
            or \
                ((not cmd_args.info) and
                    (cmd_args.topic is not None and cmd_args.out_file is not None) and
                 (not cmd_args.stats)) \
            or \
                ((not cmd_args.info) and
                 (cmd_args.topic is None and cmd_args.out_file is None) and
                 cmd_args.stats)

        if not valid:
            print('Must specify either bag info, a topic and output file, or statistics')

    return valid


def display_bag_info(bag_name):
    """ Lists every topic in the bag, and the fields within each topic. Data is sent to the standard
        output. This assumes that every message for a given topic has the same format in the bag.
        This can sometimes break. For example, if a topic has an array of geometry_msgs/Vector3 in
        it, and the first message has an empty array, the components of the Vector3 will not be
        listed. Output will typically look like the following header message published on the
        /ns/dummy topic name:

        /ns/dummy
            header
                seq
                stamp
                    secs
                    nsecs
    """

    """ Get the bag file summary info """
    bag_info = yaml.load(subprocess.Popen(
        ['rosbag', 'info', '--yaml', bag_name], stdout=subprocess.PIPE).communicate()[0])

    """ Get the topics in the bag """
    bag_topics = bag_info['topics']
    bag = rosbag.Bag(bag_name)

    """ For every topic in the bag, display its fields. Only do this once per topic """
    for topic in bag_topics:
        for _, msg, _ in bag.read_messages(topics=topic['topic']):
            """ Recursively list the fields in each message """
            print_topic_fields(topic['topic'], msg, 0)
            print('')
            break

    bag.close()

    sys.stdout.write("Found %u topics\n"%len(bag_topics))


def print_topic_fields(field_name, msg, depth):
    """ Recursive helper function for displaying information about a topic in a bag. This descends
        through the nested fields in a message, an displays the name of each level. The indentation
        increases depending on the depth of the nesting. As we recursively descend, we propagate the
        field name.

            There are three cases for processing each field in the bag.

            1.  The field could have other things in it, for example a pose's translation may have
                x, y, z components. Check for this by seeing if the message has slots.
            2.  The field could be a vector of other things. For instance, in the message file we
                could have an array of vectors, like geometry_msgs/Vector[] name. In this case,
                everything in the vector has the same format, so just look at the first message to
                extract the fields within the list.
            3.  The field could be a terminal leaf in the message, for instance the nsecs field in a
                header message. Just display the name.
    """
    if hasattr(msg, '__slots__'):
        """ This level of the message has more fields within it. Display the current
                level, and continue descending through the structure.
        """
        print(' ' * (depth * 2) + field_name)
        for slot in msg.__slots__:
            print_topic_fields(slot, getattr(msg, slot), depth + 1)
    elif isinstance(msg, list):
        """ We found a vector of field names. Display the information on the current
                level, and use the first element of the vector to display information
                about its content
        """
        if (len(msg) > 0) and hasattr(msg[0], '__slots__'):
            print(' ' * (depth * 2) + field_name + '[]')
            for slot in msg[0].__slots__:
                print_topic_fields(slot, getattr(msg[0], slot), depth + 1)
    else:
        """ We have reached a terminal leaf, i.e., and field with an actual value attached.
                Just print the name at this point.
        """
        print(' ' * (depth * 2) + field_name)


def display_stats(bag_name):
    """ Displays how many messages were published on each topic in the bag
    """
    """ Get the topics in the bag """
    bag_info = yaml.load(subprocess.Popen(
        ['rosbag', 'info', '--yaml', bag_name], stdout=subprocess.PIPE).communicate()[0])
    bag_topics = bag_info['topics']

    bag = rosbag.Bag(bag_name)

    for topic in bag_topics:
        print("Topic: " + topic['topic'])
        print("\tType: " + topic['type'])
        print("\tCount: " + str(topic['messages']))

    bag.close()

def write_to_csv(bag_name, output_name, topic_name):
    """ Entry point for writing all messages published on a topic to a CSV file """
    bag = rosbag.Bag(bag_name)
    f = open(output_name, 'w')
    """ Write the name of the fields as the first line in the header file """
    column_names = write_header_line(bag, f, topic_name)
    """ Go through the bag and and write every message for a topic out to the
            CSV file
    """
    write_topic(bag, f, topic_name, column_names)
    """ Cleanup """
    f.close()
    bag.close()


def write_header_line(bag, output_file, topic_name):
    """ Writes a comma delimited list of the field names to a file. bag is an already opened bag
        file, output_file is an output file that has already been opened, and topic name identifies
        the topic to display information about,

        The field names are written in alphabetical order.
    """
    header_column_names = []

    """ Use the first message from a topic to build the header line. Note that this
            assumes the first message has all of the fields fully defined
    """
    for _, msg, _ in bag.read_messages(topics=topic_name):
        get_field_names('', msg, header_column_names)
        break

    """ Alphabetize and write the column names to the output file, minus the leading underscore """
    header_column_names.sort()
    trimmed_names = [col[1:] for col in header_column_names]
    header_line = ','.join(trimmed_names) + '\n'
    output_file.write(header_line)

    return header_column_names


def get_field_names(prefix, msg, existing_names):
    """ Recursive helper function for writing the header line. Works on the same principle as how
        the topics' fields are listed. Instead of printing them out to standard output, the parts of
        the messages are combined with underscores. When a leaf field is encountered, the entire
        prefix is printed.
    """
    if hasattr(msg, '__slots__'):
        for slot in msg.__slots__:
            get_field_names('_'.join([prefix, slot]), getattr(msg, slot), existing_names)
    elif isinstance(msg, list) and (len(msg) > 0) and hasattr(msg[0], '__slots__'):
        for slot in msg[0].__slots__:
            get_field_names('_'.join([prefix, slot]), getattr(msg[0], slot), existing_names)
    else:
        existing_names.append(prefix)


def write_topic(bag, output_file, topic_name, column_names):
    """ Iterates over a bag, finding all the messages for a given topic.

        Begins by creating a dictionary the maps each field name to its alphabetical index, because
        the CSV file columns are alphabetized.
    """
    column_mapping = dict(zip(column_names, range(0, len(column_names))))

    """ Go through every message for a given topic, extract its data fields,
            and write it to the output file
    """
    msg_count = 1
    for _, msg, _ in bag.read_messages(topics=topic_name):
        sys.stdout.write("Writing message %u%s"%(msg_count, "\r"))
        msg_count += 1
        column_values = {}
        """ Build a dictionary of field names and their values. The field names
                match the column headers.
        """
        find_field_value('', msg, column_values, column_mapping)
        """ write the discovered values out to the file """
        write_topic_line(output_file, column_mapping, column_values)

    sys.stdout.write("Processed %u messages\n"%(msg_count -1))


def find_field_value(prefix, msg, existing_values, column_names):
    """ Gets the value for all fields. Places the outputs and their field names in the
        existing_values dictionary. Works on the principle as listing the fields in the bag info
        command.
    """
    if hasattr(msg, '__slots__'):
        for slot in msg.__slots__:
            find_field_value('_'.join([prefix, slot]),
                             getattr(msg, slot), existing_values, column_names)
    elif isinstance(msg, list) and len(msg) > 0 and hasattr(msg[0], '__slots__'):
        """ When we encounter a field in the message that is a list, we need some special
            processing. If the field name we have built up so far matches something in our column
            names, we assume that we have reached a leaf of the message, and the field contains
            actual values. In that case, join all of the values in the field for a given field into
            a list. Otherwise, the field is a nested structure of other structures, and we have to
            keep going.
        """
        for slot in msg[0].__slots__:
            new_prefix = '_'.join([prefix, slot])
            if new_prefix in column_names:
                values = []
                for x in msg:
                    values.append(getattr(x, slot))
                existing_values[new_prefix] = values
            else:
                find_field_value(prefix, getattr(msg[0], slot), existing_values, column_names)
    else:
        existing_values[prefix] = msg


def write_topic_line(output_file, column_mapping, column_values):
    """ Writes the discovered field/value pairs to the output file

        We want to write the columns in alphabetical order. Rather than resorting the columns every
        time, we use a dictionary to map a field name to an output index.
    """
    columns = len(column_mapping.keys()) * [None]

    for key in column_values.keys():
        if isinstance(column_values[key], list):
            """ Fields that have a list of values, such as ranges in a laser scan, are problematic
                for representation in a csv file. Each value in the field gets separated by an
                underscore, so that it fits in a single column. Matlab uses the underscores to split
                the values
            """
            if len(column_values[key]) > 0:
                columns[column_mapping[key]] = '_'.join([str(x) for x in column_values[key]])
            else:
                """ This handles the corner case where an empty array of arrays was in the file.
                        For example, when we have an array of geometry_msgs/Vector3 values that is
                        empty. In this case, the bag file does not have empty values for the x, y, z
                        elements. Instead, we use the field name associated with the empty values to
                        every column that should contain data for this array
                """
                for true_key in column_mapping.keys():
                    if true_key.startswith(key):
                        columns[column_mapping[true_key]] = ''
        else:
            """ Normal case of a one to one mapping between a field and a value """
            columns[column_mapping[key]] = str(column_values[key])

    """ Use the now alphabetized list of values, and join them in a single line and write it """
    line = ','.join(columns) + '\n'
    output_file.write(line)


if __name__ == "__main__":
    """ Main entry point for the function. Reads the command line arguments and performs the
        requested actions
    """
    # Parse the command line arguments
    argument_parser = build_parser()
    args = argument_parser.parse_args()
    if not validate_args(args):
        sys.exit()

    # Perform the requested actions
    if args.info:
        display_bag_info(args.bag)
    elif args.stats:
        display_stats(args.bag)
    else:
        write_to_csv(args.bag, args.out_file, args.topic)

