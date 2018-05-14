# Copyright (c) 2017 Juan Carlos Saez

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sublime
import sublime_plugin
import pprint
import re
import subprocess
import tempfile
import os
import errno
import threading


class PanbuildSettings(threading.Thread):
    def __init__(self,targets,outfiles,commands,working_directory):
        self.targets=targets
        self.outfiles=outfiles
        self.commands=commands
        self.dirname=working_directory
        self.target_number=-1
        self.window=-1
        threading.Thread.__init__(self)

    def run(self):
        self.run_panbuild(self.target_number)

    def run_panbuild(self,target_number):
        if target_number<0 or target_number>=len(self.targets):
            return 1

        active_target=self.targets[target_number]
        cmd=self.commands[active_target]
        outfile=self.outfiles[active_target]

        # write panbuild command to console
        print('Running Command: '+' '.join(cmd))
    # run command
        process = subprocess.Popen(
            cmd, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, cwd=self.dirname)
        result, error = process.communicate() #contents.encode('utf-8'))
        exitcode = process.returncode

        # handle pandoc errors
        if exitcode!=0:
            sublime.error_message('\n\n'.join([
                'Error when running:',
                ' '.join(cmd),
                error.decode('utf-8').strip()]))
            return

        # if write to file, open
        if outfile is not None:
            output_path=os.path.join(self.dirname, outfile)
            try:
                if sublime.platform() == 'osx':
                    subprocess.call(["open", output_path])
                elif sublime.platform() == 'windows':
                    os.startfile(output_path)
                elif os.name == 'posix':
                    subprocess.call(('xdg-open', output_path))
            except:
                sublime.message_dialog('Wrote to file ' + output_path)

            sublime.set_timeout(lambda: self.window.run_command('show_panel', {"panel": "console","toggle": True})   , 100)        
            return 0

        return 1

class PromptPanbuildCommand(sublime_plugin.WindowCommand):

    '''Defines the plugin command palette item.

    @see Default.sublime-commands'''

    options = []

    def retrieve_targets(self,build_file,build_file_full,working_directory,inSource=False):
        if not os.path.isfile(build_file_full):
            return (errno.ENOENT,None)

        if inSource:
            cmd=["panbuild","-Lo","-f",build_file]  
            basecmd=["panbuild","-f",build_file]
        else:
            cmd=["panbuild","-Lo"]  
            basecmd=["panbuild"]

        process = subprocess.Popen(
                cmd, shell=False, #stdin=subprocess.PIPE, 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, cwd=working_directory)
        result, error = process.communicate()
        exitcode = process.returncode

        # handle pandoc errors
        if exitcode and error:
            #print('Error when running:',join(cmd),error.decode('utf-8').strip())
            return (errno.ENOENT,None)
        else:
            lines=result.splitlines()
            targets=[]
            outfiles={}
            commands={}
            for line in lines:
                tokens=line.strip().split(b':')
                target=tokens[0].decode("utf-8")
                
                if len(tokens)!=2 or tokens[1].strip() == "":
                    continue

                outfile=tokens[1].strip().decode("utf-8")

                targets.append(target)
                outfiles[target]=outfile
                ##Create CMD
                cool_cmd=list(basecmd)
                cool_cmd.append(target)
                commands[target]=cool_cmd

            return (0,PanbuildSettings(targets,outfiles,commands,working_directory))

    def run(self):
        if self.window.active_view():
            self.window.show_quick_panel(
                self.get_build_targets(),
                self.build)

    def get_build_targets(self):
        '''Generates a ranked list of available transformations.'''
        view = self.window.active_view()

        fname=view.file_name()

        fpath=os.path.abspath(fname)

        dirname, filename=os.path.split(fpath)

        ## Search for build YAML
        buildfile=os.path.join(dirname, "build.yaml")

        (code,self.build_settings)=self.retrieve_targets("build.yaml",buildfile,dirname,inSource=False)

        if code==0: ## Buildfile was found
            print("Found build file at %s" % buildfile)
            return self.build_settings.targets

        ## try to get it from there 
        (code,self.build_settings)=self.retrieve_targets(fname,fpath,dirname,inSource=True)

        if code==0: 
            print("Found build settings in file %s" % fpath)
            return self.build_settings.targets
        else:
            sublime.error_message("No build rules found for the file")
            return ["Failed"]


    def build(self, i):
        if i == -1:
            return
        view = self.window.active_view()
        self.window.run_command('show_panel', {"panel": "console"})
        self.window.focus_view(view)
        self.build_settings.window=self.window
        version=sublime.version()
        if version[0]=='2':
            self.build_settings.target_number=i
            self.build_settings.start()
            # Dangerous...
            #sublime.set_timeout(lambda: self.build_settings.join(), 2000)
        else:
            sublime.set_timeout_async(lambda: self.build_settings.run_panbuild(i), 1)

        return 

class PromptPanbuildTargetCommand(sublime_plugin.WindowCommand):
    
    target_info = {}
    target_names=[]
    dual_mode=False

    def run( self, **kwargs ):
        if "Dual" in kwargs and kwargs["Dual"]==1:
            self.dual_mode=1

        if self.window.active_view():
            self.window.show_quick_panel(
                self.get_available_targets(),
                self.append_target)


    def get_available_targets(self):

        self.target_info = {}
        self.target_names=[]

        settings=sublime.load_settings("Panbuild.sublime-settings").get("default",None)

        if not settings:
            sublime.error_message("Settings not found")
            return None

        #print(settings)
        
        if "available-targets" in settings:
            available_targets=settings["available-targets"]
        else: 
            sublime.error_message("Settings not found")
            return []

        for target_name, settings in available_targets.items():
            self.target_names.append(target_name)
            self.target_info[target_name]=settings
        
        return self.target_names

    def append_target(self, i):  
        '''Add target to build.yaml file'''
        ## Retrieve pandoc options
        name=self.target_names[i]
        properties=self.target_info[name]

        if not "pandoc-options" in properties:
            sublime.error_message("pandoc-options not found for target %s" % name)
            return

        if not "target-id" in properties:
            sublime.error_message("Target id not found for target %s" % name)
            return

        pandoc_options=properties["pandoc-options"]
        target_id=properties["target-id"]

        ## Search for build.yaml
        view = self.window.active_view()
        fname=view.file_name()
        fpath=os.path.abspath(fname)
        dirname, filename=os.path.split(fpath)
        buildfile=os.path.join(dirname, "build.yaml")
        
        if not os.path.isfile(buildfile):
            ## Create a new build file 
            if self.dual_mode:
                cmd=["panbuild","-D","-S",filename+" "+pandoc_options,target_id]
            else:
                cmd=["panbuild","-S",filename+" "+pandoc_options,target_id]
        else:  
            cmd=["panbuild","-a",pandoc_options,target_id]
            
        process = subprocess.Popen(
            cmd, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, cwd=dirname)
        result, error = process.communicate() #contents.encode('utf-8'))
        exitcode = process.returncode

        # handle pandoc errors
        if exitcode!=0:
            sublime.error_message('\n\n'.join([
                'Error when running:',
                ' '.join(cmd),
                error.decode('utf-8').strip()]))
            return
        return  
