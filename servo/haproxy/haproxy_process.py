# Copyright 2009-2013 Eucalyptus Systems, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.
#
# Please contact Eucalyptus Systems, Inc., 6755 Hollister Ave., Goleta
# CA 93117, USA or visit http://www.eucalyptus.com/licenses/ if you need
# additional information or have any questions.

#haproxy -f haproxy.conf -p /var/run/haproxy.pid -V -D -sf $(</var/run/haproxy.pid)
import os
import subprocess
import commands
import servo
from servo.util import ServoError
from servo.config import SUDO_BIN, RUN_ROOT

class HaproxyProcess(object):
    RUNNING=0
    TERMINATED=1

    def __init__(self, haproxy_bin='/usr/local/sbin/haproxy', conf_file=None, pid_path=None):
        self.__conf_file=conf_file
        self.__pid_path=pid_path
        self.__haproxy_bin = haproxy_bin
        if not os.path.exists(haproxy_bin):
            raise ServoError("%s not found in the system" % haproxy_bin)
        if not os.path.exists(conf_file):
            raise ServoError("%s not found in the system" % conf_file)
        if self.check_haproxy_process() == 0:
            self.__status = HaproxyProcess.RUNNING
        else:
            self.__status = HaproxyProcess.TERMINATED

    def run(self):
        # make sure no other haproxy process running
        if self.__status == HaproxyProcess.RUNNING or self.check_haproxy_process() == 0:
            raise ServoError("haproxy already running")

        haproxy_cmd = '%s -f %s -p %s -V -C %s -D'.format(self.__haproxy_bin, self.__conf_file,
                                                          self.__pid_path, RUN_ROOT)

        if servo.run_as_sudo(haproxy_cmd) != 0:
            raise ServoError("failed to launch haproxy process")

        self.__status = HaproxyProcess.RUNNING

    def terminate(self):
        kill_cmd = 'kill -9 $(<%s)'.format(self.__pid_path)

        if os.path.isfile(self.__pid_path):
            servo.run_as_sudo(kill_cmd)

        if self.check_haproxy_process() == 0:
            raise ServoError("haproxy still running")
        self.__status = HaproxyProcess.TERMINATED
 
    def restart(self):
        if self.check_haproxy_process() != 0:
            servo.log.warning('on restart, no running haproxy process found')

        haproxy_cmd = '%s -f %s -p %s -V -C %s -D -sf $(<%s)'.format(self.__haproxy_bin, self.__conf_file,
                                                                     self.__pid_path, RUN_ROOT, self.__pid_path)

        if servo.run_as_sudo(haproxy_cmd) != 0:
            raise ServoError("failed to restart haproxy process")

        self.__status = HaproxyProcess.RUNNING
 
    def pid(self):
        if not os.path.exists(self.__pid_path):
            raise "pid file is not found in %s" % self.__pid_path
        if subprocess.call('ps -p $(<$s)' % self.__pid_path, shell=True) != 0:
            raise "process with pid=%s not found" % commands.get_output('cat %s' % self.__pid_path)
        pid = commands.getoutput('cat %s' % self.__pid_path)
        return pid

    def check_haproxy_process(self):
        proc = subprocess.Popen(['ps', '-C', 'haproxy'], stderr=subprocess.PIPE)
        proc.communicate()
        return proc.returncode

    def status(self):
        return self.__status