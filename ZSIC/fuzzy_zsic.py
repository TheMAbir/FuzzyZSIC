from typing import List, Union
import torch
import clip
import PIL
from PIL import Image
import requests
import numpy as np
import os
from sentence_transformers import SentenceTransformer, util
from fuzzywuzzy import fuzz

class FuzzyZeroShotImageClassification():

    def __init__(self, *args, **kwargs):
        """
        Load CLIP models based on either language needs or vision backbone needs
        With English labeling, users have the liberty to choose different vision backbones
        Multi-lingual labeling is only supported with ViT as vision backbone.

        Args:
            Model (`str`, *optional*, defaults to `ViT-B/32`):
              Any one of the CNN or Transformer based pretrained models can be used as Vision backbone.
              `RN50`, `RN101`, `RN50x4`, `RN50x16`, `RN50x64`, `ViT-B/32`, `ViT-B/16`, `ViT-L/14`
            Lang (`str`, *optional*, defaults to `en`):
              Any one of the language codes below
              ar, bg, ca, cs, da, de, el, es, et, fa, fi, fr, fr-ca, gl, gu, he, hi, hr, hu,
              hy, id, it, ja, ka, ko, ku, lt, lv, mk, mn, mr, ms, my, nb, nl, pl, pt, pt, pt-br,
              ro, ru, sk, sl, sq, sr, sv, th, tr, uk, ur, vi, zh-cn, zh-tw.
        """

        if "lang" in kwargs:
            self.lang = kwargs["lang"]
        else:
            self.lang = "en"

        lang_codes = self.available_languages()

        if self.lang not in lang_codes:
            raise Exception('Language code {} not valid, supported codes are {} '.format(self.lang, lang_codes))
            return

        device = "cuda:0" if torch.cuda.is_available() else "cpu"

        if self.lang == "en":
            model_tag = "ViT-B/32"
            if "model" in kwargs:
                model_tag = kwargs["model"]
            print("Loading OpenAI CLIP model {} ...".format(model_tag))
            self.model, self.preprocess = clip.load(model_tag, device=device)
            print("Label language {} ...".format(self.lang))
        else:
            model_tag = "clip-ViT-B-32"
            print("Loading sentence transformer model {} ...".format(model_tag))
            self.model = SentenceTransformer('clip-ViT-B-32', device=device)
            self.text_model = SentenceTransformer('sentence-transformers/clip-ViT-B-32-multilingual-v1', device=device)
            print("Label language {} ...".format(self.lang))

    def available_models(self):
        """Returns the names of available CLIP models"""
        return clip.available_models()

    def available_languages(self):
        """Returns the codes of available languages"""
        codes = """ar, bg, ca, cs, da, de, en, el, es, et, fa, fi, fr, fr-ca, gl, gu, he, hi, hr, hu,
        hy, id, it, ja, ka, ko, ku, lt, lv, mk, mn, mr, ms, my, nb, nl, pl, pt, pt, pt-br,
        ro, ru, sk, sl, sq, sr, sv, th, tr, uk, ur, vi, zh-cn, zh-tw"""
        return set([code.strip() for code in codes.split(",")])

    def _load_image(self, image: str) -> "PIL.Image.Image":
        """
        Loads `image` to a PIL Image.
        Args:
            image (`str` ):
                The image to convert to the PIL Image format.
        Returns:
            `PIL.Image.Image`: A PIL Image.
        """
        if isinstance(image, str):
            if image.startswith("http://") or image.startswith("https://"):
                image = PIL.Image.open(requests.get(image, stream=True).raw)
            elif os.path.isfile(image):
                image = PIL.Image.open(image)
            else:
                raise ValueError(
                    f"Incorrect path or url, URLs must start with `http://` or `https://`, and {image} is not a valid path"
                )
        elif isinstance(image, PIL.Image.Image):
            image = image
        else:
            raise ValueError(
                "Incorrect format used for image. Should be an url linking to an image, a local path, or a PIL image."
            )
        image = PIL.ImageOps.exif_transpose(image)
        image = image.convert("RGB")
        return image

    def fuzzy_match(self, candidate_label, labels, threshold=80):
        """
        Performs fuzzy matching with a confidence threshold.

        Args:
            candidate_label (`str`): The candidate label to match.
            labels (`List[str]`): The list of labels to compare with.
            threshold (`int`, *optional*, defaults to 80):
                The minimum fuzzy matching score (out of 100) to consider a match.

        Returns:
            A tuple containing:
                - best_match (`str`): The label with the highest fuzzy score that meets the threshold.
                - best_match_score (`int`): The fuzzy score of the best match (0-100).
        """

        best_match_score = 0
        best_match = None
        for label in labels:
            match_score = fuzz.partial_ratio(candidate_label, label)
            if match_score > best_match_score and match_score >= threshold:
                best_match_score = match_score
                best_match = label
        return best_match, best_match_score

    def __call__(self, image: str, candidate_labels: Union[str, List[str]], *args, **kwargs):
        """
        Classify the image using the candidate labels given

        Args:
            image (`str`):
                Fully Qualified path of a local image or URL of image
            candidate_labels (`str` or `List[str]`):
                The set of possible class labels to classify each sequence into. Can be a single label, a string of
                comma-separated labels, or a list of labels.
            hypothesis_template (`str`, *optional*, defaults to `"A photo of {}."`, if lang is default / `en`):
                The template used to turn each label into a string. This template must include a {} or
                similar syntax for the candidate label to be inserted into the template.
            top_k (`int`, *optional*, defaults to 5):
                The number of top labels that will be returned by the pipeline. If the provided number is higher than
                the number of labels available in the model configuration, it will default to the number of labels.

        Return:
            A `dict` or a list of `dict`: Each result comes as a dictionary with the following keys:
            - **image** (`str`) -- The image for which this is the output.
            - **scores** (`List[float]`) -- The probabilities for each of the labels.
            - **fuzzy_matched_labels** (`List[str]`) -- Fuzzy matched labels.
            - **highest_fuzzy_label** (`str`) -- The label with the highest fuzzy score.
            - **highest_score** (`float`) -- The highest score among the predicted labels.
        """

        device = "cuda:0" if torch.cuda.is_available() else "cpu"

        if self.lang == "en":
            if "hypothesis_template" in kwargs:
                hypothesis_template = kwargs["hypothesis_template"]
            else:
                hypothesis_template = "A photo of {}"

            if isinstance(candidate_labels, str):
                labels = [hypothesis_template.format(candidate_label) for candidate_label in candidate_labels.split(",")]
            else:
                labels = [hypothesis_template.format(candidate_label) for candidate_label in candidate_labels]
        else:
            if "hypothesis_template" in kwargs:
                hypothesis_template = kwargs["hypothesis_template"]
            else:
                hypothesis_template = "{}"

            if isinstance(candidate_labels, str):
                labels = [hypothesis_template.format(candidate_label) for candidate_label in candidate_labels.split(",")]
            else:
                labels = [hypothesis_template.format(candidate_label) for candidate_label in candidate_labels]

        # TO BE IMPLEMENTED
        if "top_k" in kwargs:
             top_k = kwargs["top_k"]
        else:
             top_k = len(labels)

        if str(type(self.model)) == "<class 'clip.model.CLIP'>":
            img = self.preprocess(self._load_image(image)).unsqueeze(0).to(device)
            text = clip.tokenize(labels).to(device)
            image_features = self.model.encode_image(img)
            text_features = self.model.encode_text(text)
        else:
            image_features = torch.tensor(self.model.encode(self._load_image(image)))
            text_features = torch.tensor(self.text_model.encode(labels))

        sim_scores = util.cos_sim(text_features, image_features)
        out = []
        for sim_score in sim_scores:
            out.append(sim_score.item() * 100)
        probs = torch.tensor([out])
        probs = probs.softmax(dim=-1).cpu().numpy()
        scores = list(probs.flatten())

        # Fuzzy matching with threshold
        fuzzy_matched_labels = []
        highest_fuzzy_score = 0
        highest_fuzzy_label = None
        for candidate_label in candidate_labels:
            fuzzy_matched_label, match_score = self.fuzzy_match(candidate_label, labels)
            fuzzy_matched_labels.append(fuzzy_matched_label)
            if match_score > highest_fuzzy_score:
                highest_fuzzy_score = match_score
                highest_fuzzy_label = fuzzy_matched_label

        # Handling potential false positives
        # 1. Confidence score threshold:
        if highest_fuzzy_score < 90:
            highest_fuzzy_label = None

        # 2. Combining with CLIP classification (consider this approach):
        # It can be implemented a custom logic here based on needs.
        # For example, if the highest_fuzzy_label is not among the top-k CLIP predictions,
        # consider it less reliable and prioritize the CLIP results.

        preds = {}
        preds["image"] = image
        preds["scores"] = scores
        preds["fuzzy_matched_labels"] = fuzzy_matched_labels
        preds["highest_fuzzy_label"] = highest_fuzzy_label
        preds["highest_score"] = max(scores)

        return preds
