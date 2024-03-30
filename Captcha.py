# REQURES KERAS OCR MODELS DOWLOADED / ADDED TO PATH
# Currently using craft_mlt_25k.h5 and crnn_kurapan.h5


class captcha():
    
    """
    A class for processing CAPTCHA images to identify specific characters and their locations for automated interactions.
    
    Attributes:
        image_url (str): URL of the CAPTCHA image.
        output_path (str): Path to save processed images. Defaults to '~/Documents'.
        sensitivity (int): Sensitivity threshold for image masking. Defaults to 25.
        
    Methods:
        get_image(): Downloads and processes the CAPTCHA image from the URL.
        image_masking(): Masks the image to enhance text features by converting to black and white.
        image_blur(): Applies a Gaussian blur to the masked image to reduce noise.
        single_ocr(): Performs Optical Character Recognition (OCR) on the blurred image.
        get_text_key(): Extracts recognized text from the OCR results.
        find_copy(): Identifies the first character that appears more than once in the recognized text.
        get_location(): Calculates the locations of the identified duplicate characters.
    """
    
    def __init__(self, 
                 image_url : str, 
                 output_path : str = os.path.expanduser('~/Documents'),
                 sensetivity : int = 25
                ):
        
        """
        Initializes the captcha class with the image URL, output path, and sensitivity settings, then processes the image.
        
        Parameters:
            image_url (str): The URL of the CAPTCHA image.
            image_array (array): NumPy array used for pixel manipulation.
            mask_output_path (str): The directory path where mask processed images will be saved. Defaults to '~/Documents'.
            blur_output_path (str): The directory path where masked and blurred processed images will be saved. Defaults to '~/Documents'.
            sensitivity (int): The sensitivity threshold used for image masking. Defaults to 25.
            width, height (int): Image width and height in pixels.
            ocr_key (list): List with one value (for single ocr) containing all characters found by the ocr.
            prediction_group (list): Special output from keras ocr function.
            seen_letters (set): List of exploded characters from the string found in ocr_key.
            copy (str): The character which appears twice (if there is one. Otherwise value is '').
        """
        
        self.image_url = image_url
        self.input_image = None
        self.image_array = None
        self.mask_output_path = output_path + '\\' + 'PostProcess.png'
        self.blur_output_path =  output_path + '\\' + 'PostProcessBlur.png'
        
        self.sensetivity = sensetivity
        self.width = 0
        self.height = 0
        self.ocr_key = []
        self.prediciton_group = []
        self.seen_letters = set()
        self.copy = str()
        
        self.get_image()
        self.image_masking()
        self.image_blur()
        self.single_ocr()
        self.get_text_key()
        self.find_copy()
        self.get_location()
    
    
    
    def get_image(self):
        
        """
        Downloads the CAPTCHA image from the specified URL and converts it to a format suitable for processing.
        """
        
        img = Image.open(requests.get(self.image_url, stream = True).raw)
        img = img.convert("RGB")
        # img.show()
        self.input_image = np.copy(img)
        self.width, self.height = img.size
        self.image_array = np.asarray(self.input_image)
    
        return
    
    
    
    def image_masking(self):
        
        """
        Masks the CAPTCHA image to enhance text recognition by converting the image to black and white based on a sensitivity threshold.
        """
        
        pixelmean = np.empty((self.height,self.width), dtype='int')
        whitecount = 0
        
        # This will loop through all the pixel values and remove all shadows as well as convert letters and numbers to masks (black)
        
        for r in range(0,self.height):
            for c in range(0,self.width):
                pixelmean[r][c] = np.mean(self.image_array[r][c])
                whitecount = 0
                for i in range(len(self.image_array[r][c])):
                    if (pixelmean[r][c]-self.sensetivity) < self.image_array[r][c][i] < (pixelmean[r][c]+self.sensetivity):
                        whitecount += 1
                if whitecount == 3:
                    for i in range(len(self.image_array[r][c])):
                        self.image_array[r][c][i] = 255
                else:
                    for i in range(len(self.image_array[r][c])):
                        self.image_array[r][c][i] = 0
                  
        post_process_image = Image.fromarray(np.uint8(self.image_array))
        post_process_image.save(self.mask_output_path)
        
        return

    
    
    def image_blur(self):
        
        """
        Applies a Gaussian blur to the masked image to reduce noise and improve OCR accuracy.
        """
        
        post_process_image = Image.fromarray(np.uint8(self.image_array))
        blur_image = post_process_image.filter(ImageFilter.GaussianBlur(1))
        blur_image.save(self.blur_output_path)
        
        return
    
    
    def single_ocr(self):
        
        """
        Performs OCR on the blurred image to recognize text and its bounding boxes.
        """
        
        pipeline = keras_ocr.pipeline.Pipeline()
        images = [keras_ocr.tools.read(self.blur_output_path)]
        self.prediction_group = pipeline.recognize(images)
        
        # fig, axs = plt.subplots(nrows=1, figsize=(20, 20))
        # for ax, image, predictions in zip(axs, images, prediction_groups):
        #     keras_ocr.tools.drawAnnotations(image = image, predictions = predictions, ax = ax)
        
        return
    
    
    
    def get_text_key(self):

        """
        Extracts and compiles the recognized text from the OCR results.
        """
        
        tempkey = []
        for i, box in enumerate(self.prediction_group):
            tempkey = []
            for j, pred in enumerate(box):
                tempval = str(self.prediction_group[i][j][0])
                tempkey.append(tempval)
            self.ocr_key.append("".join(tempkey))
            
        return
        
        
        
    def find_copy(self):
        
        """
        Identifies the first character in the recognized text that appears more than once, indicating a potential target for interaction.
        """
        
        self.copy = ''
        for c in self.ocr_key[0]:
            if c in self.seen_letters:
                self.copy = c
                break
            self.seen_letters.add(c)
            
        return
    
    

    def get_location(self):
        
        """
        Calculates the pixel locations of the identified duplicate character(s) in the CAPTCHA image.
        """
        
        location = []
        
        for i, box in enumerate(self.prediction_group):
            
            for j, pred in enumerate(box):
                
                # Becuase the ocr sometimes groups some letters together in a box (ex. 'ce' vs. 'c', 'e'), they must be separated in order to get an accurate location for each individual letter
                
                charlist = list(self.prediction_group[i][j][0])
                length = len(charlist)
                
                for k, indchar in enumerate(charlist):
                    
                    if indchar == self.copy:
                        
                        # This code covers all cases of ocr grouping. See previous note
                        
                        loc = np.asarray(self.prediction_group[i][j][1])
                        txseg = (loc[1][0]-loc[0][0])/length
                        tyseg = (loc[1][1]-loc[0][1])/length
                        tlbox = [loc[0][0] + (txseg*k), loc[0][1] + (tyseg*k)]
                        trbox = [loc[0][0] + (txseg*(k+1)), loc[0][1] + (tyseg*(k+1))]
                        bxseg = (loc[2][0]-loc[3][0])/length
                        byseg = (loc[2][1]-loc[3][1])/length
                        blbox = [loc[3][0] + (txseg*k), loc[3][1] + (tyseg*k)]
                        brbox = [loc[3][0] + (txseg*(k+1)), loc[3][1] + (tyseg*(k+1))]
                        centeradj = [tlbox,trbox,brbox,blbox]
                        xlist = [centeradj[c][0] for c, i in enumerate(centeradj)]
                        ylist = [centeradj[c][1] for c, i in enumerate(centeradj)]
                        xavg = np.mean(xlist)
                        yavg = np.mean(ylist)
                        clickcoord = [xavg,yavg]
                        location.append(clickcoord)
                        
        return location
