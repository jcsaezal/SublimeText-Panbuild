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

def run_panbuild_command(cmd,dirname):
    # write panbuild command to console
    print('Running Command: '+' '.join(cmd))
    # run command
    process = subprocess.Popen(
            cmd, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, cwd=dirname)
    result, error = process.communicate() #contents.encode('utf-8'))
    exitcode = process.returncode

    # handle panbuild errors
    if exitcode!=0:
        sublime.error_message('\n\n'.join([
            'Error when running:',
            ' '.join(cmd),
            error.decode('utf-8').strip()]))
           
    return exitcode


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

        exitcode=run_panbuild_command(cmd,self.dirname)

        if exitcode !=0:
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
    action="build-target"
    build_settings=None

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

        #print(self.action)
        if self.action=="remove-target":
            ## Filter lists...
            f_targets=[]
            f_outfiles={}
            f_commands={}

            prev="777"
            for target in targets:
                idx=target.rfind("/")
                if idx==-1:
                    f_target=target
                else:    
                    f_target=target[:idx]

                ## Add if not repeated
                if f_target!=prev:
                    f_targets.append(f_target)
                    f_outfiles[f_target]=outfiles[target]
                    f_commands[f_target]=commands[target]

                prev=f_target

            ## Replace unfiltered data structures with filtered ones
            targets=f_targets
            outfiles=f_outfiles
            commands=f_commands

            print(targets)

        return (0,PanbuildSettings(targets,outfiles,commands,working_directory))

    def run(self, **kwargs ):
        if "action" in kwargs:
            self.action=kwargs["action"]
        else:
            self.action="build-target"

        self.build_settings=None

        print(self.action)
        if self.action=="remove-target":
            action_function=self.remove_target
        else:
            action_function=self.build

        if self.window.active_view():
            self.window.show_quick_panel(
                self.get_build_targets(),
                action_function)

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

        if self.action == "remove-target":
            return []

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

    def remove_target(self,i):
        if i == -1:
            return 
         
        target_name=self.build_settings.targets[i]
        cmd=["panbuild","-r",target_name]
        
        process = subprocess.Popen(
          cmd, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
          stderr=subprocess.PIPE, cwd=self.build_settings.dirname)

        result, error = process.communicate()
        exitcode = process.returncode

        # handle panbuild errors
        if exitcode!=0:
            sublime.error_message('\n\n'.join([
                'Error when running:',
                ' '.join(cmd),
                error.decode('utf-8').strip()]))
            return

class PromptPanbuildTargetCommand(sublime_plugin.WindowCommand):
    
    target_info = {}
    target_names=[]
    dual_mode=False
    action=None
    cmd=[]
    dirname=None

    def build_yaml_is_present(self):
        ## Search for build.yaml
        view = self.window.active_view()
        fname=view.file_name()
        fpath=os.path.abspath(fname)
        dirname, filename=os.path.split(fpath)
        buildfile=os.path.join(dirname, "build.yaml")
        return (os.path.isfile(buildfile),dirname)

    def run( self, **kwargs ):
        if "Dual" in kwargs and kwargs["Dual"]==1:
            self.dual_mode=1

        if "action" in kwargs:
            self.action=kwargs["action"]

        (build_yaml_found,dirname)=self.build_yaml_is_present()

        if  self.action=="create-file":
            ##Ask if overwriting is in order
            if build_yaml_found:
                if sublime.yes_no_cancel_dialog("Found existing build.yaml file.\nDo you want to overwrite it?")!=1:
                    return
        elif self.action=="delete-file":
            if not build_yaml_found:
                sublime.error_message("build.yaml was not found at %s" % dirname)
                return
            os.remove(os.path.join(dirname, "build.yaml"))
            return
        elif self.action=="open-file":
            if not build_yaml_found: 
                sublime.error_message("build.yaml was not found at %s" % dirname)
                return     
            self.window.open_file(os.path.join(dirname, "build.yaml"))
            return 
        elif self.action=="clean":
            if not build_yaml_found:
                sublime.error_message("build.yaml was not found at %s" % dirname)
                return
            self.cmd=["panbuild","clean"]
            self.dirname=dirname
            self.invoke_panbuild_command()     
            return               
        else: ## Add-target...  
            if not build_yaml_found and sublime.yes_no_cancel_dialog("build.yaml was not found at %s.\nDo you want to create it?" % dirname) !=1:
                    return 

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
        
        ## Add custom target
        self.target_names.append("Custom target")   
        self.target_info["Custom target"]={"target-id": "","pandoc-options":""}

        return self.target_names

    def invoke_panbuild_command(self):
        return run_panbuild_command(self.cmd,self.dirname)

    def create_custom_target(self,user_input):
        lastarg=self.cmd[-1]
        self.cmd[-1]=lastarg+user_input
        self.cmd.append("CUSTOM")
        return self.invoke_panbuild_command()

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
        fname=self.window.active_view().file_name()
        fpath=os.path.abspath(fname)
        dirpath, filename=os.path.split(fpath)

        ## Search for build.yaml
        (build_yaml_found,self.dirname)=self.build_yaml_is_present()

        if self.action=="create-file":
            ## Create a new build file overwriting it if necessary
            if self.dual_mode:
                self.cmd=["panbuild","-D","-S",filename+" "+pandoc_options]
            else:
                self.cmd=["panbuild","-S",filename+" "+pandoc_options]
        elif self.action=="add-target":
            self.cmd=["panbuild","-a",pandoc_options]
            
        if target_id!="":
            self.cmd.append(target_id)        
            self.invoke_panbuild_command()
        else:
            self.window.show_input_panel("Indicate the options to be passed to pandoc", "",self.create_custom_target, None, None)      
