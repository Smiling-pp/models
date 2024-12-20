import sys
import math
import mindspore as ms
from mindspore import ops

from can.models.backbones import build_backbone
from can.models.heads import build_head
from can.models import build_model


sys.path.append(".")
ms.set_context(mode=ms.PYNATIVE_MODE, pynative_synchronize=True, jit_config={"jit_level": "O0"})


def test_can_model():
    """
        Test function description
        This test case is mainly tested in three aspects:
        1. Test the build_model of the complete model
        2. build_backbone unit test
        3. build_head unit test

        Local test code adjustment:
        You need to change ckpt_load_path to the weight file path in the local directory
    """

    # model parameter setting
    model_config = {
        "backbone": {
            "name": "rec_can_densenet",
            "pretrained": False,
            "growth_rate": 24, 
            "reduction": 0.5, 
            "bottleneck": True, 
            "use_dropout": True,
            "input_channels": 1,
            },
        "neck": {
            },
        "head": {
            "name": "CANHead",
            "out_channels": 111,
            "ratio": 16,
            "attdecoder": {
                "is_train": True,
                "input_size": 256,
                "hidden_size": 256,
                "encoder_out_channel": 684,
                "dropout": True,
                "dropout_ratio": 0.5,
                "word_num": 111,
                "counting_decoder_out_channel": 111,
                "attention": {
                        "attention_dim": 512,
                        "word_conv_kernel": 1,
                    },
                },
            },
    }


    # test case parameter settings
    batch_size = 1
    input_tensor_channel = 1
    images_mask_channel = 1
    num_steps = 10
    word_num = 111
    out_channels = 111
    h = 132
    w = 519

    input_tensor = ops.randn((batch_size, input_tensor_channel, h, w))
    images_mask = ops.ones((batch_size, images_mask_channel, h, w))
    labels = ops.randint(low=0, high=word_num, size=(batch_size, num_steps))

    # basemodel unit test
    model_config.pop("neck")
    # model = build_model(model_config, ckpt_load_path=ckpt_load_path)
    model = build_model(model_config)
    input = list()
    input.append(input_tensor)
    input.append(images_mask)
    input.append(labels)
    hout = model(*input)

    assert hout["word_probs"].shape == (batch_size, num_steps, word_num), "Word probabilities shape is incorrect"
    assert hout["counting_preds"].shape == (batch_size, out_channels), "Counting predictions shape is incorrect"
    assert hout["counting_preds1"].shape == (batch_size, out_channels), "Counting predictions 1 shape is incorrect"
    assert hout["counting_preds2"].shape == (batch_size, out_channels), "Counting predictions 2 shape is incorrect"

    # build_backbone unit test
    backbone_name = model_config["backbone"].pop("name")
    backbone = build_backbone(backbone_name, **model_config["backbone"])
    bout = backbone(input_tensor)

    bout_c = backbone.out_channels[-1] #The paper specified 684 features to be extracted
    bout_h = math.ceil(h/model_config["head"]["ratio"])
    bout_w = math.ceil(w/model_config["head"]["ratio"])
    assert bout_c == 684, "bout channel is incorrect"
    assert bout.shape == (batch_size, bout_c, bout_h, bout_w), "bout shape is incorrect"

    # build_head unit test
    head_name = model_config["head"].pop("name")
    head = build_head(head_name, in_channels=bout_c, **model_config["head"])
    head_args = ((images_mask, labels))
    hout = head(bout, head_args)

    assert hout["word_probs"].shape == (batch_size, num_steps, word_num), "Word probabilities shape is incorrect"
    assert hout["counting_preds"].shape == (batch_size, out_channels), "Counting predictions shape is incorrect"
    assert hout["counting_preds1"].shape == (batch_size, out_channels), "Counting predictions 1 shape is incorrect"
    assert hout["counting_preds2"].shape == (batch_size, out_channels), "Counting predictions 2 shape is incorrect"


if __name__ == "__main__":
    test_can_model()
