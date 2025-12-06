class Solution(object):
    def twoSum(nums, target):
        """
        :type nums: List[int]
        :type target: int
        :rtype: List[int]
        """
        for (key, m) in enumerate(nums):
            for (key2, n) in enumerate(nums[key+1:]):
                if m + n == target and key != key2+key+1:
                    print([key, key2 + key+1])


if __name__ == "__main__":
    Solution.twoSum(nums=[3,  3], target=6)
