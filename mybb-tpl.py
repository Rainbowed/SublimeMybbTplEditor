# Sublime Plugin: Mybb Template Editor
# Author: Mihai Ionut Vilcu (ionutvmi@gmail.com)
# Aug 2013
# Because sublime is awesome !!!

import sublime, sublime_plugin, subprocess, os, sys, time, urllib.request, urllib.parse, re, codecs

ESCAPE_SEQUENCE_RE = re.compile(r'''
    ( \\U........      # 8-digit hex escapes
    | \\u....          # 4-digit hex escapes
    | \\x..            # 2-digit hex escapes
    | \\[0-7]{1,3}     # Octal escapes
    | \\N\{[^}]+\}     # Unicode characters by name
    | \\[\\'"abfnrtv]  # Single-character escapes
    )''', re.UNICODE | re.VERBOSE)

class MybbTplLoadCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        self.settings = sublime.load_settings("mybb-tpl.sublime-settings")
        self.show_panel() # we prompt the user for tpl set


    def load_tpls(self, path):
        px = self.settings.get('table_prefix')
        sid = self.settings.get('tpl_set')

        # select all tpl names
        files = self.run_query("SELECT `title` FROM `"+px+"templates` WHERE `sid`='"+ sid +"' OR `sid` = '-2' ORDER BY sid DESC, title ASC")
        files.pop(0) # rempve the first element

        prefixes = self.run_query("SELECT `prefix` FROM `"+px+"templategroups`")
        prefixes.append("ungrouped")

        [os.mkdir(path + "/" + p) for p in prefixes if not os.path.exists(path + "/" + p)]

        # select all templates
        templates = self.run_query("SELECT `template` FROM `"+px+"templates` WHERE `sid`='"+ sid +"' OR `sid` = '-2' ORDER BY sid DESC, title ASC")
        templates.pop(0) # rempve the first element

        tmp = []

        # for each template we make a file and write the template text inside
        for idx,val in enumerate(files):
            if val not in tmp:
                tmp.append(val)

                t = val.split('_').pop(0)

                with open(path + "/" + ("ungrouped" if t not in prefixes else t) + "/" + val + ".mybbtpl", 'wb+') as f:
                    f.write(bytes(templates[idx], "UTF-8"))

        # clean some stuff
        del files, templates, tmp

        self.openInNewWindow(path)


    def create_folder(self, folder_name):
        # we build the mybb-tpl folder
        if sublime.platform() == "windows":
            path = os.path.expanduser("~\\My Documents\\" + folder_name)
        else:
            path = os.path.expanduser("~/Documents/" + folder_name)

        if not os.path.exists(path):
            os.makedirs(path)

        self.load_tpls(path) # we download the tpls from db

    def show_panel(self):
        prefix = self.settings.get('table_prefix')
        titles = self.run_query("SELECT `title` FROM `"+prefix+"templatesets`")

        titles.pop(0) # remove the first row

        self.view.window().show_quick_panel(titles, self.setTplSet)

    def setTplSet(self, p):
        if p < 0:
            return False;

        prefix = self.settings.get('table_prefix')

        tplSets = self.run_query("SELECT `sid` FROM `"+prefix+"templatesets`")
        tplSets.pop(0) # remove the first row

        self.settings.set('tpl_set', tplSets[p])
        sublime.save_settings("mybb-tpl.sublime-settings")

        #grab the folder name
        self.view.window().show_input_panel("Folder name:", "mybbTpl", self.create_folder, None, None)

    def run_query(self, query):
        if query is None:
            return False

        self.settings = sublime.load_settings("mybb-tpl.sublime-settings")

        mysql = self.settings.get('mysql_executable', 'mysql')
        host = self.settings.get('host', "localhost")
        dbname = self.settings.get('dbname')
        user = self.settings.get('user')
        passwd = self.settings.get('passwd')
        encoding = self.settings.get('encoding', 'utf8')

        # if password is empty we don't include it
        if passwd == '':
            conarray = [mysql, '--default-character-set=' + encoding, '-u', user, '-h', host, dbname, "-e %s" % query]
        else:
            conarray = [mysql, '--default-character-set=' + encoding, '-u', user, '-p%s' % passwd, '-h', host, dbname, "-e %s" % query]

        conarray = [x for x in conarray if x is not None]

        startupinfo = None

        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        process = subprocess.Popen(conarray, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=startupinfo)

        lines = process.stdout.readlines()

        stdout = [self.decode_escapes(x.decode(encoding).rstrip()) for x in lines]

        if self.settings.get('passwd') != '' and stdout != []:
            stdout.pop(0) # remove the warning

        if 'ERROR ' in ''.join(stdout):
            sublime.error_message(''.join(stdout))

        return stdout

    def openInNewWindow(self, path):
        subprocess.Popen([sublime.executable_path(), '.'], cwd=path, shell=False)

    def decode_escapes(self, s):
        if s is None:
            return False

        def decode_match(match):
            return codecs.decode(match.group(0), 'unicode-escape')

        return ESCAPE_SEQUENCE_RE.sub(decode_match, s)

class MybbCssLoadCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        self.m = MybbTplLoadCommand(self.view)
        self.settings = sublime.load_settings("mybb-tpl.sublime-settings")
        self.show_panel() # we prompt the user for a css set


    def load_css(self, path):
        px = self.settings.get('table_prefix')
        tid = self.settings.get('css_set')

        # select all css names
        files = self.m.run_query("SELECT `name` FROM `"+px+"themestylesheets` WHERE `tid`='"+ tid +"' ORDER BY name ASC")
        files.pop(0)
        # select all stylesheets
        stylesheets = self.m.run_query("SELECT `stylesheet` FROM `"+px+"themestylesheets` WHERE `tid`='"+ tid +"' ORDER BY name ASC")
        stylesheets.pop(0)

        tmp = []
        # for each template we make a file and write the template text inside
        for idx,val in enumerate(files):
            if val not in tmp:
                tmp.append(val)
                f = open(path+"/"+val+".mybbcss", 'wb+')
                f.write(bytes(stylesheets[idx], "UTF-8"))
                f.close()

        # clean some stuff
        del files, stylesheets, tmp

        self.openInNewWindow(path)


    def create_folder(self, folder_name):
        # we build the mybb-tpl folder
        if sublime.platform() == "windows":
            path = os.path.expanduser("~\\My Documents\\" + folder_name)
        else:
            path = os.path.expanduser("~/Documents/" + folder_name)

        if not os.path.exists(path):
            os.makedirs(path)

        self.load_css(path) # we download the csses from db

    def show_panel(self):
        prefix = self.settings.get('table_prefix')
        names = self.m.run_query("SELECT `name` FROM `"+prefix+"themes`")

        names.pop(0) # remove the first row

        self.view.window().show_quick_panel(names, self.setCssSet)

    def setCssSet(self, p):
        if p < 0:
            return False

        prefix = self.settings.get('table_prefix')

        cssSets = self.m.run_query("SELECT `tid` FROM `"+prefix+"themes`")
        cssSets.pop(0) # remove the first row

        self.settings.set('css_set', cssSets[p])
        sublime.save_settings("mybb-tpl.sublime-settings")

        #grab the folder name
        self.view.window().show_input_panel("Folder name:", "mybbCss", self.create_folder, None, None)

    def openInNewWindow(self, path):
        subprocess.Popen([sublime.executable_path(), '.'], cwd=path, shell=True)


#check for updating the existing tpls and update them if they are edited

class MybbTplUpdate(sublime_plugin.EventListener):
    def on_post_save(self, view):
        self.settings = sublime.load_settings("mybb-tpl.sublime-settings")
        path = view.file_name()
        fileName = os.path.basename(path)
        ext = os.path.splitext(fileName)[1]

        if(ext == '.mybbtpl'):
            name = os.path.splitext(fileName)[0]
            self.updateTpl(name, view)
        elif(ext == '.mybbcss'):
            name = os.path.splitext(fileName)[0]
            self.updateCss(name, view)


    def updateTpl(self, name, view):
        sid = self.settings.get('tpl_set')
        prefix = self.settings.get('table_prefix')
        ver = self.settings.get('mybb_version')
        m = MybbTplLoadCommand(view)

        # get the content of this file
        content = re.escape(view.substr(sublime.Region(0, view.size())))

        # we check if this template exists for the current set
        check = m.run_query("SELECT `tid` FROM `"+prefix+"templates` WHERE `title` = '"+name+"' AND `sid` = '"+sid+"'")
        if check == []:
            result = m.run_query("INSERT INTO `"+prefix+"templates` SET `title` = '"+name+"', `template`= '"+content+"', `sid` = '"+sid+"', `version`='"+ver+"'")
        else:
            result = m.run_query("UPDATE `"+prefix+"templates` SET `template`= '"+content+"' WHERE `title` = '"+name+"' AND `sid` = '"+sid+"'")

        if not result:
            sublime.status_message("Template successfully updated!")
        else:
            print(result)

    def updateCss(self, name, view):
        if self.settings.get('css_password') == "":
            return sublime.error_message("Enter a password into the updatecss.php file and package settings")
            
        tid = self.settings.get('css_set')

        content = view.substr(sublime.Region(0, view.size()))

        postdata = urllib.parse.urlencode({"name" : name, "tid" : tid, "stylesheet" : content, "password": self.settings.get('css_password')})

        f = urllib.request.urlopen(self.settings.get('css_update_url'), postdata.encode('utf-8')).read()

        if str(f).find('Invalid password') != -1:
            sublime.error_message("Invalid CSS password")
        else:
            sublime.status_message("CSS successfully updated!")
