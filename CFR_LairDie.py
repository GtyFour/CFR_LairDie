import random

# 常量定义
DOUBT = 0
ACCEPT = 1

class Node:
    """CFR 信息集节点"""
    def __init__(self, num_actions):
        self.regret_sum = [0.0] * num_actions
        self.strategy = [0.0] * num_actions
        self.strategy_sum = [0.0] * num_actions
        self.u = 0.0           # 当前节点的效用
        self.p_player = 0.0    # 当前玩家到达概率
        self.p_opponent = 0.0  # 对手到达概率

    def get_strategy(self):
        """根据遗憾值计算当前策略（归一化）"""
        normalizing_sum = 0.0
        for a in range(len(self.strategy)):
            self.strategy[a] = max(self.regret_sum[a], 0.0)
            normalizing_sum += self.strategy[a]
        if normalizing_sum > 0:
            for a in range(len(self.strategy)):
                self.strategy[a] /= normalizing_sum
        else:
            # 均匀分布
            for a in range(len(self.strategy)):
                self.strategy[a] = 1.0 / len(self.strategy)
        # 累加策略到策略和（用于平均策略）
        for a in range(len(self.strategy)):
            self.strategy_sum[a] += self.p_player * self.strategy[a]
        return self.strategy

    def get_average_strategy(self):
        """返回平均策略（训练结束后使用）"""
        normalizing_sum = sum(self.strategy_sum)
        if normalizing_sum > 0:
            return [s / normalizing_sum for s in self.strategy_sum]
        else:
            return [1.0 / len(self.strategy_sum)] * len(self.strategy_sum)


class LiarDieTrainer:
    def __init__(self, sides=6):
        self.sides = sides

        # 初始化 response 节点: response[myClaim][oppClaim] 表示当上一个叫点为 myClaim，
        # 对手叫了 oppClaim 后，当前玩家面临质疑/接受决策的节点。
        # myClaim 和 oppClaim 的取值范围：0 <= myClaim < oppClaim <= sides-1
        self.response_nodes = [[None] * sides for _ in range(sides)]
        for my_claim in range(sides):
            for opp_claim in range(my_claim + 1, sides):
                self.response_nodes[my_claim][opp_claim] = Node(2)  # 两个动作：质疑和接受

        # 初始化 claim 节点: claim[oppClaim][roll] 表示当前叫点为 oppClaim 时，
        # 当前玩家骰子为 roll，需要选择新叫点的节点。
        # oppClaim 取值范围 0..sides-1，roll 取值范围 1..sides
        self.claim_nodes = [[None] * (sides + 1) for _ in range(sides)]
        for opp_claim in range(sides):
            for roll in range(1, sides + 1):
                num_actions = sides - opp_claim  # 可叫 opp_claim+1 到 sides，共 sides-opp_claim 种
                self.claim_nodes[opp_claim][roll] = Node(num_actions)

    def train(self, iterations):
        # 存储每次迭代中每个旧叫点对应的当前玩家骰子点数（注意：逻辑上不合理，但保持原设计）
        roll_after_accepting = [0] * self.sides

        for it in range(iterations):
            # --- 1. 初始化骰子和概率 ---
            for i in range(self.sides):
                roll_after_accepting[i] = random.randint(1, self.sides)

            # 设置初始节点：旧叫点为0，当前玩家骰子为 roll_after_accepting[0]
            init_node = self.claim_nodes[0][roll_after_accepting[0]]
            init_node.p_player = 1.0
            init_node.p_opponent = 1.0

            # --- 2. 前向传播 ---
            for opp_claim in range(self.sides):
                # 2.1 访问 response 节点（当 opp_claim > 0 时）
                if opp_claim > 0:
                    for my_claim in range(opp_claim):  # 所有小于 opp_claim 的 my_claim
                        node = self.response_nodes[my_claim][opp_claim]
                        if node is None:
                            continue
                        action_prob = node.get_strategy()
                        # 如果选择接受（索引1），则转移到 claim 节点
                        if action_prob[ACCEPT] > 0:
                            next_node = self.claim_nodes[opp_claim][roll_after_accepting[opp_claim]]
                            next_node.p_player += action_prob[ACCEPT] * node.p_player
                            next_node.p_opponent += node.p_opponent

                # 2.2 访问 claim 节点（当 opp_claim < sides 时）
                if opp_claim < self.sides:
                    node = self.claim_nodes[opp_claim][roll_after_accepting[opp_claim]]
                    if node is None:
                        continue
                    action_prob = node.get_strategy()
                    # 对于每个可能的叫点 my_claim (opp_claim+1 到 sides)
                    for idx, my_claim in enumerate(range(opp_claim + 1, self.sides + 1)):
                        if action_prob[idx] > 0:
                            next_node = self.response_nodes[opp_claim][my_claim]
                            # 注意：叫点者变为对手，所以交换概率
                            next_node.p_player += node.p_opponent
                            next_node.p_opponent += action_prob[idx] * node.p_player

            # --- 3. 反向传播（计算效用和遗憾） ---
            regret = [0.0] * self.sides  # 临时存储

            for opp_claim in range(self.sides - 1, -1, -1):
                # 3.1 访问 claim 节点（后向）
                if opp_claim < self.sides:
                    node = self.claim_nodes[opp_claim][roll_after_accepting[opp_claim]]
                    if node is None:
                        continue
                    action_prob = node.strategy  # 使用当前策略（已经计算过）
                    node.u = 0.0
                    # 计算每个子节点的效用
                    for idx, my_claim in enumerate(range(opp_claim + 1, self.sides + 1)):
                        next_node = self.response_nodes[opp_claim][my_claim]
                        child_util = -next_node.u   # 因为对手的效用取反
                        regret[idx] = child_util
                        node.u += action_prob[idx] * child_util
                    # 更新遗憾
                    for a in range(len(action_prob)):
                        regret[a] -= node.u
                        node.regret_sum[a] += node.p_opponent * regret[a]
                    # 清零概率
                    node.p_player = node.p_opponent = 0.0

                # 3.2 访问 response 节点（后向）
                if opp_claim > 0:
                    for my_claim in range(opp_claim):  # 所有小于 opp_claim 的 my_claim
                        node = self.response_nodes[my_claim][opp_claim]
                        if node is None:
                            continue
                        action_prob = node.strategy
                        node.u = 0.0
                        # 质疑动作的效用
                        if opp_claim > roll_after_accepting[my_claim]:
                            doubt_util = 1.0
                        else:
                            doubt_util = -1.0
                        regret[DOUBT] = doubt_util
                        node.u += action_prob[DOUBT] * doubt_util

                        # 接受动作的效用（转移到 claim 节点）
                        if opp_claim < self.sides:
                            next_node = self.claim_nodes[opp_claim][roll_after_accepting[opp_claim]]
                            regret[ACCEPT] = next_node.u
                            node.u += action_prob[ACCEPT] * next_node.u

                        # 更新遗憾
                        for a in range(len(action_prob)):
                            regret[a] -= node.u
                            node.regret_sum[a] += node.p_opponent * regret[a]
                        # 清零概率
                        node.p_player = node.p_opponent = 0.0

            # --- 4. 重置策略和（用于平均策略，后半段开始重置）---
            if it == iterations // 2:
                for i in range(self.sides):
                    for j in range(self.sides):
                        if self.response_nodes[i][j] is not None:
                            self.response_nodes[i][j].strategy_sum = [0.0] * len(self.response_nodes[i][j].strategy_sum)
                    for roll in range(1, self.sides + 1):
                        if self.claim_nodes[i][roll] is not None:
                            self.claim_nodes[i][roll].strategy_sum = [0.0] * len(self.claim_nodes[i][roll].strategy_sum)

        # --- 5. 打印结果 ---
        print("=" * 60)
        print("训练完成，平均策略如下：")
        print("=" * 60)

        # 初始叫点策略（旧叫点为0，不同初始骰子点数下的策略）
        print("\n初始叫点策略（旧叫点=0）:")
        for roll in range(1, self.sides + 1):
            node = self.claim_nodes[0][roll]
            avg_strat = node.get_average_strategy()
            print(f"  初始骰子 {roll}: ", end="")
            for idx, prob in enumerate(avg_strat):
                new_claim = idx + 1  # 因为动作索引0对应叫点1
                print(f"叫{new_claim}:{prob:.3f} ", end="")
            print()

        # 响应策略（质疑/接受）
        print("\n响应策略（当对手叫点更高时，选择质疑或接受的概率）:")
        for my_claim in range(self.sides):
            for opp_claim in range(my_claim + 1, self.sides):
                node = self.response_nodes[my_claim][opp_claim]
                avg_strat = node.get_average_strategy()
                print(f"  当前叫点 {my_claim}, 对手叫 {opp_claim} -> 质疑:{avg_strat[DOUBT]:.3f}, 接受:{avg_strat[ACCEPT]:.3f}")

        # 叫点策略（给定旧叫点和骰子点数，选择新叫点的概率）
        print("\n叫点策略（给定旧叫点和骰子点数）:")
        for opp_claim in range(self.sides):
            for roll in range(1, self.sides + 1):
                node = self.claim_nodes[opp_claim][roll]
                avg_strat = node.get_average_strategy()
                if max(avg_strat) < 0.01:  # 跳过几乎均匀的策略
                    continue
                print(f"  旧叫点 {opp_claim}, 骰子 {roll}: ", end="")
                for idx, prob in enumerate(avg_strat):
                    new_claim = opp_claim + 1 + idx
                    if new_claim <= self.sides:
                        print(f"叫{new_claim}:{prob:.3f} ", end="")
                print()


if __name__ == "__main__":
    trainer = LiarDieTrainer(sides=6)
    trainer.train(iterations=100000)  # 可以调高到 1000000 获得更稳定结果
