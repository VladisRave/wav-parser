import tensorflow as tf
import tensorflow_hub as hub

_model = None
_class_names = None


def load_model():
    """
    Загружает модель YAMNet и список классов.

    Модель загружается один раз (singleton pattern),
    далее используется из памяти.

    Returns:
        model: загруженная YAMNet модель
        class_names: список аудио-классов
    """
    global _model, _class_names
    if _model is not None:
        return _model, _class_names

    # Определяем устройство
    if tf.config.list_physical_devices('GPU'):
        device = '/GPU:0'
        print("Используем GPU")
    else:
        device = '/CPU:0'
        print("GPU не найден, используем CPU")

    with tf.device(device):
        print("Загрузка YAMNet...")
        _model = hub.load("https://tfhub.dev/google/yamnet/1")

    # Загрузка классов (без изменений)
    class_map_path = _model.class_map_path().numpy().decode('utf-8')
    _class_names = []
    with open(class_map_path) as f:
        next(f)
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 3:
                _class_names.append(parts[2])
    print("YAMNet загружена")
    return _model, _class_names