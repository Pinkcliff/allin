import LuMoSDKClient
import csv
from datetime import datetime
import time
import os

ip = "192.168.3.24"

# 数据超时设置（秒）
DATA_TIMEOUT = 5  # 如果5秒内没有收到新数据，自动退出程序

# 动态CSV管理变量
current_csv_file = None
current_writer = None
current_marker_count = 0  # 当前CSV记录的标记点数量
current_frame_count = 0   # 当前CSV已记录的帧数
total_frame_count = 0     # 总帧数


def create_new_csv_file(marker_count):
    """创建新的CSV文件"""
    global current_csv_file, current_writer, current_marker_count, current_frame_count

    # 关闭旧CSV文件（如果存在）
    if current_csv_file is not None:
        current_csv_file.close()
        print(f"\n>>> CSV文件已保存: {current_csv_file.name} (共{current_frame_count}帧)")
        print(f">>> 标记点数量变化: {current_marker_count} -> {marker_count}，创建新文件 <<<\n")

    # 生成新文件名（带时间戳和点数标记）
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_filename = f"LuMo_Data_{timestamp}_markers{marker_count}.csv"

    # 创建新CSV文件
    current_csv_file = open(csv_filename, 'w', newline='', encoding='utf-8-sig')
    current_writer = csv.writer(current_csv_file)
    current_marker_count = marker_count
    current_frame_count = 0

    # 动态生成表头（根据实际点数）
    headers = [
        '帧ID', '时间戳', '相机同步时间(原始)', '相机同步时间(可读)', '数据广播时间(原始)', '数据广播时间(可读)',
    ]

    # 添加标记点列（动态生成）
    for i in range(1, marker_count + 1):
        headers.extend([
            f'标记{i}_ID', f'标记{i}_名称', f'标记{i}_X', f'标记{i}_Y', f'标记{i}_Z'
        ])

    # 添加刚体列（固定2个刚体）
    headers.extend([
        '刚体1_ID', '刚体1_名称', '刚体1_追踪状态', '刚体1_X', '刚体1_Y', '刚体1_Z',
        '刚体1_qx', '刚体1_qy', '刚体1_qz', '刚体1_qw', '刚体1_质量等级',
        '刚体1_速度', '刚体1_X速度', '刚体1_Y速度', '刚体1_Z速度',
        '刚体1_加速度', '刚体1_X加速度', '刚体1_Y加速度', '刚体1_Z加速度',
        '刚体1_X欧拉角', '刚体1_Y欧拉角', '刚体1_Z欧拉角',
        '刚体2_ID', '刚体2_名称', '刚体2_追踪状态', '刚体2_X', '刚体2_Y', '刚体2_Z',
        '刚体2_qx', '刚体2_qy', '刚体2_qz', '刚体2_qw', '刚体2_质量等级',
        '时码_时', '时码_分', '时码_秒', '时码_帧', '时码_子帧',
    ])

    current_writer.writerow(headers)
    print(f">>> 新CSV文件已创建: {csv_filename} (支持{marker_count}个标记点) <<<")

print(f"数据超时设置: {DATA_TIMEOUT}秒无数据将自动退出")
print("开始记录数据...")
print(">>> 标记点数量变化时，会自动创建新的CSV文件 <<<")

LuMoSDKClient.Init()
LuMoSDKClient.Connnect(ip)

last_data_time = time.time()  # 记录最后一次收到数据的时间

try:
    while True:
        # 检查是否超时
        current_time = time.time()
        if current_time - last_data_time > DATA_TIMEOUT:
            print(f"\n!!! 超过 {DATA_TIMEOUT} 秒未收到数据，发送方可能已停止 !!!")
            print("程序自动退出...")
            break

        frame = LuMoSDKClient.ReceiveData(0) # 0 :阻塞接收 1：非阻塞接收
        if frame is None:
            continue

        # 收到数据，更新时间戳
        last_data_time = time.time()
        total_frame_count += 1

        # ========== 检查标记点数量，决定是否需要创建新CSV ==========
        current_marker_num = len(frame.markers)

        # 第一次收到数据，或者点数增多时，创建新CSV
        if current_csv_file is None or current_marker_num > current_marker_count:
            create_new_csv_file(current_marker_num)

        # ========== 命令行输出（带中文标注） ==========
        FrameID = frame.FrameId
        print(f"帧ID: {FrameID}") #打印帧ID
        TimeStamp = frame.TimeStamp
        print(f"当前帧时间戳: {TimeStamp}") #打印当前帧时间戳
        uCameraSyncTime = frame.uCameraSyncTime
        # 转换成可读时间（微秒时间戳）
        camera_sync_readable = datetime.fromtimestamp(uCameraSyncTime / 1000000).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        print(f"相机同步时间: {uCameraSyncTime} ({camera_sync_readable})") #打印相机同步时间
        uBroadcastTime = frame.uBroadcastTime
        # 转换成可读时间
        broadcast_readable = datetime.fromtimestamp(uBroadcastTime / 1000000).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        print(f"数据广播时间: {uBroadcastTime} ({broadcast_readable})") #打印数据广播时间
        markers = frame.markers
        for marker in markers:
            print(f"标记ID: {marker.Id}")  #打印散点ID
            print(f"标记名称: {marker.Name}") #打印散点名称
            print(f"X坐标: {marker.X}")  #打印散点的坐标数据 :X
            print(f"Y坐标: {marker.Y}")  #打印散点的坐标数据 :Y
            print(f"Z坐标: {marker.Z}")  #打印散点的坐标数据 :Z
        for rigid in frame.rigidBodys:
            if rigid.IsTrack is True: #判断刚体追踪状态
                print(f"刚体ID: {rigid.Id}")  #打印刚体ID
                print(f"刚体名称: {rigid.Name}") #打印刚体名称
                print(f"X坐标: {rigid.X}")  #打印刚体坐标信息：X
                print(f"Y坐标: {rigid.Y}")  #打印刚体坐标信息：Y
                print(f"Z坐标: {rigid.Z}")  #打印刚体坐标信息：Z
                print(f"qx姿态: {rigid.qx}")  #打印刚体姿态信息：qx
                print(f"qy姿态: {rigid.qy}")  #打印刚体姿态信息：qy
                print(f"qz姿态: {rigid.qz}")  #打印刚体姿态信息：qz
                print(f"qw姿态: {rigid.qw}")  #打印刚体姿态信息：qw
                print(f"质量等级: {rigid.QualityGrade}")   #打印刚体质量等级
                print(f"速度: {rigid.speeds.fSpeed}")  #打印刚体速度
                print(f"X轴速度: {rigid.speeds.XfSpeed}") #打印刚体x轴方向速度
                print(f"Y轴速度: {rigid.speeds.YfSpeed}") #打印刚体y轴方向速度
                print(f"Z轴速度: {rigid.speeds.ZfSpeed}") #打印刚体z轴方向速度
                print(f"加速度: {rigid.acceleratedSpeeds.fAcceleratedSpeed}")  #打印刚体加速度
                print(f"X轴加速度: {rigid.acceleratedSpeeds.XfAcceleratedSpeed}") #打印刚体x轴方向加速度
                print(f"Y轴加速度: {rigid.acceleratedSpeeds.YfAcceleratedSpeed}") #打印刚体y轴方向加速度
                print(f"Z轴加速度: {rigid.acceleratedSpeeds.ZfAcceleratedSpeed}") #打印刚体z轴方向加速度
                print(f"X轴欧拉角: {rigid.eulerAngle.X}")  #打印x轴欧拉角
                print(f"Y轴欧拉角: {rigid.eulerAngle.Y}")  #打印y轴欧拉角
                print(f"Z轴欧拉角: {rigid.eulerAngle.Z}")  #打印z轴欧拉角
                print(f"X轴角速度: {rigid.palstance.fXPalstance}") #打印x轴角速度
                print(f"Y轴角速度: {rigid.palstance.fYPalstance}") #打印y轴角速度
                print(f"Z轴角速度: {rigid.palstance.fZPalstance}") #打印z轴角速度
                print(f"X轴角加速度: {rigid.accpalstance.AccfXPalstance}") #打印x轴角加速度
                print(f"Y轴角加速度: {rigid.accpalstance.AccfYPalstance}") #打印y轴角加速度
                print(f"Z轴角加速度: {rigid.accpalstance.AccfZPalstance}") #打印z轴角加速度
            else:
                print(f"刚体ID(未追踪): {rigid.Id}")  #打印刚体ID

        for skeleton in frame.skeletons:
            if skeleton.IsTrack is True:
                print(f"人体ID: {skeleton.Id}")   #打印人体ID
                print(f"人体名称: {skeleton.Name}") #打印人体名称
                for bone in skeleton.skeletonBones:
                    print(f"  骨骼ID: {bone.Id}")   #打印人体内骨骼ID
                    print(f"  骨骼名称: {bone.Name}") #打印人体内骨骼名称
                    print(f"  X坐标: {bone.X}")    #打印人体内骨骼坐标：X
                    print(f"  Y坐标: {bone.Y}")    #打印人体内骨骼坐标：Y
                    print(f"  Z坐标: {bone.Z}")    #打印人体内骨骼坐标：Z
                    print(f"  qx姿态: {bone.qx}")   #打印人体内骨骼姿态：qx
                    print(f"  qy姿态: {bone.qy}")   #打印人体内骨骼姿态：qy
                    print(f"  qz姿态: {bone.qz}")   #打印人体内骨骼姿态：qz
                    print(f"  qw姿态: {bone.qw}")   #打印人体内骨骼姿态：qw
                print(f"机器人名称: {skeleton.RobotName}") #打印机器人名称
                for Key in skeleton.MotorAngle:
                    print(f"  电机名称: {Key}")         #打印机器人电机名称
                    print(f"  电机角度: {skeleton.MotorAngle[Key]}")  #打印机器人电机角度值
            else:
                print(f"人体ID(未追踪): {skeleton.Id}")   #打印人体ID
        for markerset in frame.markerSet:
            print(f"点集名称: {markerset.Name}")  #打印点集名称
            for marker in markerset.markers:
                print(f"  点ID: {marker.Id}")   #打印点集内点ID
                print(f"  点名称: {marker.Name}") #打印点集内点名称
                print(f"  X坐标: {marker.X}")    #打印点集内点坐标：X
                print(f"  Y坐标: {marker.Y}")    #打印点集内点坐标：Y
                print(f"  Z坐标: {marker.Z}")    #打印点集内点坐标：Z

        #时码信息
        print(f"时码-时: {frame.timeCode.mHours}")   #打印时码：时
        print(f"时码-分: {frame.timeCode.mMinutes}") #打印时码：分
        print(f"时码-秒: {frame.timeCode.mSeconds}") #打印时码：秒
        print(f"时码-帧: {frame.timeCode.mFrames}")  #打印时码：帧
        print(f"时码-子帧: {frame.timeCode.mSubFrame}")#打印时码：子帧

        #自定义骨骼信息
        for CustomSkeleton in frame.customSkeleton:
            print(f"自定义骨骼ID: {CustomSkeleton.Id}")  #打印自定义骨骼ID
            print(f"自定义骨骼名称: {CustomSkeleton.Name}") #打印自定义骨骼名称
            print(f"自定义骨骼类型: {CustomSkeleton.Type}") #打印自定义骨骼类型
            for JointData in CustomSkeleton.customSkeletonBones:
                print(f"  关节ID: {JointData.Id}")   #打印自定义骨骼内骨骼ID
                print(f"  关节名称: {JointData.Name}") #打印自定义骨骼内骨骼名称
                print(f"  X坐标: {JointData.X}")    #打印自定义骨骼内骨骼坐标：X
                print(f"  Y坐标: {JointData.Y}")    #打印自定义骨骼内骨骼坐标：Y
                print(f"  Z坐标: {JointData.Z}")    #打印自定义骨骼内骨骼坐标：Z
                print(f"  qx姿态: {JointData.qx}")   #打印自定义骨骼内骨骼姿态：qx
                print(f"  qy姿态: {JointData.qy}")   #打印自定义骨骼内骨骼姿态：qy
                print(f"  qz姿态: {JointData.qz}")   #打印自定义骨骼内骨骼姿态：qz
                print(f"  qw姿态: {JointData.qw}")   #打印自定义骨骼内骨骼姿态：qw
                print(f"  置信度: {JointData.Confidence}")  #打印自定义骨骼内骨骼置信度
                print(f"  X轴姿态角: {JointData.AngleX}")  #打印自定义骨骼内骨骼姿态角：X
                print(f"  Y轴姿态角: {JointData.AngleY}")  #打印自定义骨骼内骨骼姿态角: Y
                print(f"  Z轴姿态角: {JointData.AngleZ}")  #打印自定义骨骼内骨骼姿态角: Z

        newForceplate = frame.ForcePlate
        for Key in newForceplate.ForcePlateData:
            print(f"测力台ID: {Key}")         #打印测力台ID
            print(f"  Fx力: {newForceplate.ForcePlateData[Key].Fx}")  #打印测力台矢量力的分量：Fx
            print(f"  Fy力: {newForceplate.ForcePlateData[Key].Fy}")  #打印测力台矢量力的分量：Fy
            print(f"  Fz力: {newForceplate.ForcePlateData[Key].Fz}")  #打印测力台矢量力的分量：Fz
            print(f"  X力矩: {newForceplate.ForcePlateData[Key].Mx}")  #力矩：X
            print(f"  Y力矩: {newForceplate.ForcePlateData[Key].My}")  #力矩：Y
            print(f"  Z力矩: {newForceplate.ForcePlateData[Key].Mz}")  #力矩：Z
            print(f"  X压心坐标: {newForceplate.ForcePlateData[Key].Lx}")  #压心坐标
            print(f"  Z压心坐标: {newForceplate.ForcePlateData[Key].Lz}")  #压心坐标

        # ========== CSV数据写入 ==========
        # 收集当前帧的所有数据
        row_data = []

        # 基础帧信息
        # 转换时间为可读格式（微秒时间戳）
        camera_sync_readable = datetime.fromtimestamp(frame.uCameraSyncTime / 1000000).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        broadcast_readable = datetime.fromtimestamp(frame.uBroadcastTime / 1000000).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

        row_data.extend([
            frame.FrameId,           # 帧ID
            frame.TimeStamp,         # 时间戳
            frame.uCameraSyncTime,   # 相机同步时间（原始）
            camera_sync_readable,    # 相机同步时间（可读）
            frame.uBroadcastTime,    # 数据广播时间（原始）
            broadcast_readable,      # 数据广播时间（可读）
        ])

        # 标记数据（根据当前CSV的点数动态写入）
        markers_list = list(frame.markers)
        for i in range(current_marker_count):
            if i < len(markers_list):
                m = markers_list[i]
                row_data.extend([m.Id, m.Name, m.X, m.Y, m.Z])
            else:
                # 如果实际点数少于CSV的点数，用空值填充
                row_data.extend(['', '', '', '', ''])

        # 刚体数据（最多2个刚体，刚体1记录详细信息）
        rigids_list = list(frame.rigidBodys)
        for i in range(2):
            if i < len(rigids_list):
                r = rigids_list[i]
                if i == 0 and r.IsTrack:  # 刚体1记录详细信息
                    row_data.extend([
                        r.Id, r.Name, 1 if r.IsTrack else 0, r.X, r.Y, r.Z,
                        r.qx, r.qy, r.qz, r.qw, r.QualityGrade,
                        r.speeds.fSpeed, r.speeds.XfSpeed, r.speeds.YfSpeed, r.speeds.ZfSpeed,
                        r.acceleratedSpeeds.fAcceleratedSpeed,
                        r.acceleratedSpeeds.XfAcceleratedSpeed,
                        r.acceleratedSpeeds.YfAcceleratedSpeed,
                        r.acceleratedSpeeds.ZfAcceleratedSpeed,
                        r.eulerAngle.X, r.eulerAngle.Y, r.eulerAngle.Z,
                    ])
                else:  # 刚体2只记录基本信息
                    row_data.extend([r.Id, r.Name, 1 if r.IsTrack else 0, r.X, r.Y, r.Z,
                        '', '', '', '', ''])
            else:
                if i == 0:
                    row_data.extend(['', '', '', '', '', '', '', '', '', '', '',
                        '', '', '', '', '', '', '', '', '', '', ''])
                else:
                    row_data.extend(['', '', '', '', '', '', '', '', ''])

        # 时码信息
        row_data.extend([
            frame.timeCode.mHours,
            frame.timeCode.mMinutes,
            frame.timeCode.mSeconds,
            frame.timeCode.mFrames,
            frame.timeCode.mSubFrame,
        ])

        # 写入CSV
        current_writer.writerow(row_data)
        current_frame_count += 1

        # 每100帧打印一次进度
        if total_frame_count % 100 == 0:
            print(f"=== 已记录 {total_frame_count} 帧数据 (当前文件: {current_frame_count}帧, {current_marker_count}个点) ===")

except KeyboardInterrupt:
    print("\n用户手动中断程序...")
except Exception as e:
    print(f"\n程序异常: {e}")
finally:
    # 清理资源
    LuMoSDKClient.Close()

    # 关闭当前CSV文件
    if current_csv_file is not None:
        current_csv_file.close()
        print(f"\n>>> 最终CSV文件已保存: {current_csv_file.name} (共{current_frame_count}帧) <<<")

    print(f"\n数据记录完成，共 {total_frame_count} 帧")
    print("程序已正常退出")