from Captcha import *

imageurl = r'https://p16-security-va.ibyteimg.com/img/security-captcha-oversea-usa/3d_092418976144eee136f15fcbf0eb9fa57ab79370_1_2.jpg~tplv-obj.image'

# The get_location() function returns the coordinates of the doubles. This information can be used by an automated browser to pass this type of captcha.

def main():
    c1 = captcha(image_url = imageurl)
    coords = c1.get_location()
    
    

if __name__ == '__main__':
    main()
