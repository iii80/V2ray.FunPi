# encoding: utf-8
"""
File:       v2ray_controller
Author:     twotrees.us@gmail.com
Date:       2020年7月30日  31周星期四 10:53
Desc:
"""
import subprocess
import requests
import sys
from .v2ray_user_config import V2RayUserConfig
from .v2ray_config import V2RayConfig
from .v2ray_default_path import V2rayDefaultPath

class V2rayController:
    def start(self) -> bool:
        cmd = "systemctl start v2ray.service; supervisorctl start v2ray"
        subprocess.check_output(cmd, shell=True).decode('utf-8')
        return self.running()

    def stop(self) -> bool:
        cmd = "systemctl stop v2ray.service; supervisorctl stop v2ray"
        subprocess.check_output(cmd, shell=True).decode('utf-8')
        return not self.running()

    def restart(self) -> bool:
        cmd = "systemctl restart v2ray.service; supervisorctl restart v2ray"
        subprocess.check_output(cmd, shell=True).decode('utf-8')
        return self.running()

    def running(self) -> bool:
        cmd = """ps -ef | grep "v2ray" | grep -v grep | awk '{print $2}'"""
        output = subprocess.check_output(cmd, shell=True).decode('utf-8')
        if output == "":
            return False
        else:
            return True

    def version(self) -> str:
        v2ray_path = 'v2ray'
        cmd_get_current_ver = """echo `{0} -version 2>/dev/null` | head -n 1 | cut -d " " -f2""".format(v2ray_path)
        current_ver = 'v' + subprocess.check_output(cmd_get_current_ver, shell=True).decode('utf-8').replace('\n', '')

        return current_ver

    def check_new_version(self) -> str:
        r = requests.get('https://api.github.com/repos/v2fly/v2ray-core/releases/latest')
        r = r.json()
        version = r['tag_name']
        return version

    def update(self) -> bool:
        update_log = subprocess.check_output("bash ./script/update_v2ray.sh", shell=True).decode('utf-8')
        ret = update_log.find('installed')
        if ret:
            ret = self.restart()

        return ret

    def access_log(self) -> str:
        lines = self.tailf(V2rayDefaultPath.access_log() , 10)
        return lines.replace('\n', '<br>')

    def error_log(self) -> str:
        lines = self.tailf(V2rayDefaultPath.error_log(), 10)
        return lines.replace('\n', '<br>')

    def tailf(self, file, count)->str:
        lines = subprocess.check_output("tail -n {0} {1}".format(count, file), shell=True).decode('utf-8')
        return  lines

    def apply_node(self, user_config:V2RayUserConfig) -> bool:
        config = V2RayConfig.gen_config(user_config)
        return self.apply_config(config)

    def apply_config(self, config: str) -> bool:
        with open(V2rayDefaultPath.config_file(), 'w+') as f:
            f.write(config)

        result = self.restart()
        return  result

    def enable_iptables(self):
        subprocess.check_output("bash ./script/config_iptable.sh", shell=True)
        subprocess.check_output("systemctl enable v2ray_iptable.service", shell=True)

class MacOSV2rayController(V2rayController):
    def start(self) -> bool:
        cmd = "brew services start v2ray-core"
        subprocess.check_output(cmd, shell=True).decode('utf-8')
        return self.running()

    def stop(self) -> bool:
        cmd = "brew services stop v2ray-core"
        subprocess.check_output(cmd, shell=True).decode('utf-8')
        return not self.running()

    def restart(self) -> bool:
        cmd = "brew services restart v2ray-core"
        subprocess.check_output(cmd, shell=True).decode('utf-8')
        return self.running()

    def update(self) -> bool:
        update_log = subprocess.check_output("brew upgrade v2ray-core", shell=True).decode('utf-8')
        ret = update_log.find('built in')
        if ret:
            ret = self.restart()

        return ret

    def enable_iptables(self):
        return

def make_controller():
    if sys.platform == 'darwin':
        return MacOSV2rayController()
    else:
        return V2rayController()