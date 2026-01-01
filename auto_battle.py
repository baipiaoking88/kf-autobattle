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
        
        # 统计不同类型敌人的击败次数
        self.enemy_stats = {}
        
        # 统计战斗结果
        self.battle_wins = 0
        
    
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
                    print(f"[初始化] 成功获取 safeid: {self.safeid}")
                    return True
                else:
                    print("[错误] 无法在页面中找到 safeid")
                    return False
        except requests.exceptions.RequestException as e:
            print(f"[错误] 获取 safeid 时发生网络错误: {e}")
            return False
    
    def parse_enemy_info(self, response_text):
        import re
        
        match = re.search(r'\[([^\]]+[的级])\](?=NPC)', response_text)
        
        if match:
            enemy_type = match.group(1)
            if enemy_type.endswith('级'):
                return f"{enemy_type}NPC"  # BOSS
            else:
                return f"{enemy_type}NPC"  # 其他NPC
        
        return None
    
    def check_battle_status(self):
        """检查战斗状态"""
        index_url = f"{self.base_url}/kf_fw_ig_index.php"
        try:
            response = self.session.get(index_url)
            if response.status_code == 200:
                content = response.text
                
                # 检查是否有"今日战斗已完成"的消息
                if "今日战斗已完成,请重置后再战。" in content:
                    print("[状态] 今日战斗已全部完成,需要重置后才能继续战斗")
                    return "completed"
                
                # 检查是否有战斗日志
                if "pk_log_ul" in content:
                    # 查找战斗日志中的信息
                    if "被击败" in content or "输了" in content:
                        print("[状态] 角色已被击败,无法继续战斗")
                        return "defeated"
                
                return "available"
        except requests.exceptions.RequestException as e:
            print(f"[错误] 检查战斗状态时发生网络错误: {e}")
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
            
            if battle_response.text == "no":
                print("[战斗] 服务器返回 'no',无法执行战斗")
                return "no_action"
            elif battle_response.text.strip():
                # 解析战斗结果
                response_text = battle_response.text.strip()
                
                # 识别敌人类型
                enemy_type = self.parse_enemy_info(response_text)
                enemy_info = f" 对手类型: {enemy_type}" if enemy_type else ""
                
                # 记录敌人类型统计
                if enemy_type:
                    if enemy_type not in self.enemy_stats:
                        self.enemy_stats[enemy_type] = 0
                    self.enemy_stats[enemy_type] += 1
                else:
                    if "未知" not in self.enemy_stats:
                        self.enemy_stats["未知"] = 0
                    self.enemy_stats["未知"] += 1
                
                # 判断战斗结果
                if "失败" in response_text or "lose" in response_text.lower() or "defeat" in response_text.lower() or "被击败" in response_text:
                    print(f"[战斗] ✗ 战斗失败{enemy_info}")
                    return "battle_loss"
                elif "胜利" in response_text or "win" in response_text.lower():
                    print(f"[战斗] ✓ 战斗胜利{enemy_info}")
                    self.battle_wins += 1
                    return "success"
                elif "遭遇了" in response_text:
                    print(f"[战斗] ✓ 战斗完成{enemy_info}")
                    self.battle_wins += 1
                    return "success"
                else:
                    if enemy_type:
                        print(f"[战斗] 战斗响应 - 对手类型: {enemy_type}")
                    else:
                        preview = response_text[:80] + "..." if len(response_text) > 80 else response_text
                        print(f"[战斗] 收到响应({len(response_text)} 字符): {preview}")
                return "success"
            else:
                print("[错误] 战斗请求返回空响应")
                return "empty"
                
        except requests.exceptions.RequestException as e:
            print(f"[错误] 执行战斗时发生网络错误: {e}")
            return "error"
    
    def run_continuous_battle(self):
        """运行持续战斗直到被击败或无法继续"""
        print("\n" + "="*50)
        print("    连续自动战斗系统启动中...")
        print("="*50 + "\n")
        
        # 检查初始战斗状态
        status = self.check_battle_status()
        print(f"[初始化] 当前战斗状态: {status}")
        
        if status == "completed":
            print("[终止] 今日战斗已全部完成,无法开始连续战斗")
            return
        
        if status == "defeated":
            print("[终止] 角色已被击败,无法开始连续战斗")
            return
        
        # 获取safeid
        if not self.get_safeid():
            print("[错误] 无法获取 safeid,无法继续战斗")
            return
        
        battle_count = 0
        max_battles = 240  # 设置最大战斗次数以防止无限循环
        
        try:
            while battle_count < max_battles:
                # 执行单次战斗
                result = self.perform_single_battle()
                
                if result == "no_action":
                    print("\n[检测] 无法继续战斗,正在检查具体原因...")
                    # 再次检查状态以确定原因
                    final_status = self.check_battle_status()
                    if final_status == "defeated":
                        print("[检测结果] 角色已被击败")
                        print("[终止] 停止连续战斗")
                    elif final_status == "completed":
                        print("[检测结果] 当日战斗已全部完成")
                        print("[终止] 停止连续战斗")
                    elif final_status == "available":
                        # 状态显示可用，但服务器返回'no'，说明达到每日战斗次数上限
                        print("[检测结果] 当日战斗次数已用尽")
                        print("[终止] 停止连续战斗")
                    else:
                        print("[检测结果] 未知原因,可能需要手动检查")
                        print("[终止] 停止连续战斗")
                    break
                elif result == "battle_loss":
                    # 战斗失败，继续下一场
                    battle_count += 1
                    print(f"\n[进度] 第 {battle_count} 场战斗已完成(失败),等待 2 秒后进行下一场...")
                    time.sleep(2)
                elif result == "error":
                    print("[终止] 战斗过程中发生错误,停止连续战斗")
                    break
                elif result == "success":
                    battle_count += 1
                    print(f"\n[进度] 第 {battle_count} 场战斗已完成,等待 2 秒后进行下一场...")
                    
                    # 等待一段时间再进行下一次战斗
                    time.sleep(2)
                    
                    # 检查是否被击败
                    current_status = self.check_battle_status()
                    if current_status == "defeated":
                        print("\n[检测] 角色已被击败")
                        print("[终止] 停止连续战斗")
                        break
                    elif current_status == "completed":
                        print("\n[检测] 当日战斗已全部完成")
                        print("[终止] 停止连续战斗")
                        break
        
        except KeyboardInterrupt:
            print("\n[中断] 用户手动终止战斗")
        
        print("\n" + "="*50)
        print(f"    连续战斗已结束 - 共完成 {self.battle_wins} 场战斗")
        print("="*50)
        
        # 显示敌人类型统计
        if self.enemy_stats:
            print("\n【敌人类型统计】")
            for enemy_type, count in sorted(self.enemy_stats.items(), key=lambda x: x[1], reverse=True):
                print(f"  • {enemy_type}: {count} 次")
        
        print("")

# 运行连续战斗自动化
if __name__ == "__main__":
    battle_bot = ContinuousBattleAutomation()
    battle_bot.run_continuous_battle()
