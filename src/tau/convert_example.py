"""
Tau谱面转换示例
"""

import osupyparser
from .convertor import convert_osu_file
from .beatmap import TauBeatmap


def convert_osu_to_tau(osu_file_path: str) -> TauBeatmap:
    """
    将.osu文件转换为TauBeatmap
    
    Args:
        osu_file_path: .osu文件路径
        
    Returns:
        TauBeatmap: 转换后的Tau谱面对象
    """
    # 解析.osu文件
    osu_file = osupyparser.OsuFile(file_path=osu_file_path)
    
    # 转换为TauBeatmap
    tau_beatmap = convert_osu_file(osu_file)
    
    return tau_beatmap


def main():
    """主函数示例"""
    # 示例用法（需要提供实际的.osu文件路径）
    # tau_beatmap = convert_osu_to_tau("example.osu")
    # print(f"转换完成: {tau_beatmap}")
    # print("谱面统计信息:")
    # for stat in tau_beatmap.get_statistics():
    #     print(f"  {stat.name}: {stat.content}")
    pass


if __name__ == "__main__":
    main()