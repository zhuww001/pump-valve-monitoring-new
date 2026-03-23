#!/usr/bin/env python3
"""
训练LSTM模型的脚本
"""
import os
from lstm_model import LSTMModel


def train_lstm_model():
    """训练LSTM模型"""
    # 创建模型实例
    model_path = os.path.join(os.path.dirname(__file__), 'models', 'lstm_model.keras')
    lstm_model = LSTMModel(sequence_length=10, model_path=model_path)
    
    # 生成合成数据
    print("生成合成数据...")
    synthetic_data = lstm_model.generate_synthetic_data(samples=1000)
    print(f"生成了{len(synthetic_data)}条合成数据")
    
    # 训练模型
    print("开始训练模型...")
    training_results = lstm_model.train(synthetic_data, epochs=100, batch_size=32)
    
    print("\n训练结果:")
    print(f"训练损失: {training_results['loss']:.4f}")
    print(f"验证损失: {training_results['val_loss']:.4f}")
    print(f"训练MAE: {training_results['mae']:.4f}")
    print(f"验证MAE: {training_results['val_mae']:.4f}")
    
    print(f"\n模型已保存到: {model_path}")
    
    # 测试模型
    print("\n测试模型...")
    test_data = synthetic_data[-20:]
    
    # 测试预测
    prediction = lstm_model.predict(test_data[:-1])
    print(f"预测值: {prediction}")
    print(f"实际值: [{test_data[-1]['pressure']}, {test_data[-1]['flow']}, {test_data[-1]['temperature']}]")
    
    # 测试异常检测
    is_anomaly, score, details = lstm_model.detect_anomaly(test_data)
    print(f"\n异常检测:")
    print(f"是否异常: {is_anomaly}")
    print(f"异常评分: {score:.4f}")
    print(f"预测值: {details['prediction']}")
    print(f"实际值: {details['actual']}")
    print(f"误差: {details['error']}")


if __name__ == "__main__":
    # 创建模型目录
    os.makedirs(os.path.join(os.path.dirname(__file__), 'models'), exist_ok=True)
    train_lstm_model()
