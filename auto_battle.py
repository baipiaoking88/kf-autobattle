import requests
import json
import time
import re

class ContinuousBattleAutomation:
    def __init__(self):
        # 读取cookies
        with open('session_cookies.json', 'r') as f:
            cookies_dict = json.load(f)

        # 创建session并设置cookies
        self.session = requests.Session()
        self.session.cookies.update(cookies_dict)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://bbs.kfpromax.com/kf_fw_ig_index.php',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest'
        })
        
        self.safeid = None
        self.base_url = "https://bbs.kfpromax.com"
    
    def get_safeid(self):
        """从主页获取safeid"""
        index_url = f"{self.base_url}/kf_fw_ig_index.php"
        try:
            response = self.session.get(index_url)
            if response.status_code == 200:
                # 从页面中提取safeid
                safeid_match = re.search(r'safeid=([a-f0-9]+)', response.text)
                if safeid_match:
                    self.safeid = safeid_match.group(1)
                    print(f"Found safeid: {self.safeid}")
                    return True
                else:
                    print("Could not find safeid in page")
                    return False
        except requests.exceptions.RequestException as e:
            print(f"Error getting safeid: {e}")
            return False
    
    def check_battle_status(self):
        """检查战斗状态"""
        index_url = f"{self.base_url}/kf_fw_ig_index.php"
        try:
            response = self.session.get(index_url)
            if response.status_code == 200:
                content = response.text
                
                # 检查是否有"今日战斗已完成"的消息
                if "今日战斗已完成，请重置后再战。" in content:
                    print("Today's battles are completed. Need to reset before battling again.")
                    return "completed"
                
                # 检查是否有战斗日志
                if "pk_log_ul" in content:
                    # 查找战斗日志中的信息
                    if "被击败" in content or "输了" in content:
                        print("Character has been defeated based on page content.")
                        return "defeated"
                
                return "available"
        except requests.exceptions.RequestException as e:
            print(f"Error checking battle status: {e}")
            return "error"
    
    def perform_single_battle(self):
        """执行单次战斗请求"""
        if not self.safeid:
            if not self.get_safeid():
                return False
        
        battle_url = f"{self.base_url}/kf_fw_ig_intel.php"
        post_data = {
            'safeid': self.safeid
        }
        
        try:
            battle_response = self.session.post(battle_url, data=post_data)
            print(f"Battle request Status Code: {battle_response.status_code}")
            
            if battle_response.text == "no":
                print("Response indicates no battle action is possible (possibly daily limit reached or defeated)")
                return "no_action"
            elif battle_response.text.strip():
                print(f"Battle action response received: {len(battle_response.text)} characters")
                return "success"
            else:
                print("Empty response from battle request")
                return "empty"
                
        except requests.exceptions.RequestException as e:
            print(f"Error performing battle: {e}")
            return "error"
    
    def run_continuous_battle(self):
        """运行持续战斗直到被击败或无法继续"""
        print("=== Continuous Battle Automation Starting ===")
        
        # 检查初始战斗状态
        status = self.check_battle_status()
        print(f"Initial battle status: {status}")
        
        if status == "completed":
            print("Today's battles are completed. Cannot start continuous battle.")
            return
        
        if status == "defeated":
            print("Character appears to be defeated. Cannot start continuous battle.")
            return
        
        # 获取safeid
        if not self.get_safeid():
            print("Failed to get safeid, cannot proceed with battle.")
            return
        
        battle_count = 0
        max_battles = 240  # 设置最大战斗次数以防止无限循环
        
        try:
            while battle_count < max_battles:
                # 执行单次战斗
                result = self.perform_single_battle()
                
                if result == "no_action":
                    print("Cannot continue battle - received 'no' response.")
                    # 再次检查状态以确定原因
                    final_status = self.check_battle_status()
                    if final_status == "defeated":
                        print("Character has been defeated. Stopping continuous battle.")
                    elif final_status == "completed":
                        print("Daily battle limit reached. Stopping continuous battle.")
                    break
                elif result == "error":
                    print("Error occurred during battle. Stopping continuous battle.")
                    break
                else:
                    battle_count += 1
                    print(f"Battle #{battle_count} completed. Waiting 2 seconds before next battle...")
                    
                    # 等待一段时间再进行下一次战斗
                    time.sleep(2)
                    
                    # 检查是否被击败
                    current_status = self.check_battle_status()
                    if current_status == "defeated":
                        print("Character has been defeated. Stopping continuous battle.")
                        break
                    elif current_status == "completed":
                        print("Daily battle limit reached. Stopping continuous battle.")
                        break
        
        except KeyboardInterrupt:
            print("\\nBattle interrupted by user.")
        
        print(f"Continuous battle ended. Total battles performed: {battle_count}")

# 运行持续战斗自动化
if __name__ == "__main__":
    battle_bot = ContinuousBattleAutomation()
    battle_bot.run_continuous_battle()
