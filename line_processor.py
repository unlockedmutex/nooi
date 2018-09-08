import dateutil


class LineProcessor():
    def __init__(self):
        self.next_id = 0
        pass

    def process_line(self, line):
        self.next_id += 1
        return str(self.next_id) + ' | ' + line


class HerokuLineProcessor(LineProcessor):
    def __init__(self, filters=set()):
        self.filters = set()
        self.longest_dyno_name = 0
        self.next_id = 0
        pass

    def process_line(self, line):
        elements = line.split(' ')
        found_time = False
        print_line = []
        for filt in self.filters:
            if filt not in line:
                return ''

        if line == '':
            return ''

        print_line.append(str(self.next_id))
        self.next_id += 1
        time = dateutil.parser.parse(elements[0])
        formatted_time = '<seagreen>' + time.strftime(
            "%Y-%m-%d %H:%M:%S") + '</seagreen>'
        print_line.append(formatted_time)
        source, dyno = elements[1][:-2].split('[')
        formatted_source = '<red>' + source + '</red>'
        print_line.append(formatted_source)
        if len(dyno) > self.longest_dyno_name:
            self.longest_dyno_name = len(dyno)
            formatted_dyno = '<lightblue>' + dyno + '</lightblue>'
        else:
            formatted_dyno = '<lightblue>' + dyno + ' ' * (
                self.longest_dyno_name - len(dyno)) + '</lightblue>'
        print_line.append(formatted_dyno)
        print_line.append(' '.join(elements[2:]))

        return " | ".join(print_line)
