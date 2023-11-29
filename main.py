import streamlit as st
import streamlit_authenticator as stauth
from dependancies import sign_up, fetch_users
from pydub import AudioSegment
import io
from pathlib import Path
import select
from shutil import rmtree
import subprocess as sp
import sys
from typing import Dict, Tuple, Optional,IO
import os
from st_audiorec import st_audiorec
import librosa
import noisereduce as nr
import soundfile as sf
import IPython.display as ipd
import streamlit_lottie

st.set_page_config(page_title='Streamlit', page_icon='🐍', initial_sidebar_state='collapsed')


# Design move app further up and remove top padding
st.markdown('''<style>.css-1egvi7u {margin-top: -3rem;}</style>''',
            unsafe_allow_html=True)
# Design change st.Audio to fixed height of 45 pixels
st.markdown('''<style>.stAudio {height: 45px;}</style>''',
            unsafe_allow_html=True)
# Design change hyperlink href link color
st.markdown('''<style>.css-v37k9u a {color: #ff4c4b;}</style>''',
            unsafe_allow_html=True)  # darkmode
st.markdown('''<style>.css-nlntq9 a {color: #ff4c4b;}</style>''',
            unsafe_allow_html=True)  # lightmode

def noise():
    uploaded_file = st.file_uploader("Upload an audio file (WAV format)", type=["wav"])

    if uploaded_file is not None:
        st.subheader("Original Audio")
        audio, sample_rate = librosa.load(uploaded_file)

        # Play the original audio
        st.audio(audio, format="audio/wav", sample_rate=sample_rate)

        # Apply noise reduction
        st.subheader("Enhanced Audio (Noise Reduction)")

        # Reduce noise in the audio
        reduced_noise = nr.reduce_noise(y=audio, sr=sample_rate)

        # Play the enhanced audio
        st.audio(reduced_noise, format="audio/wav", sample_rate=sample_rate)

        # Save enhanced audio to a file
        st.subheader("Download Enhanced Audio")
        if st.button("Download Enhanced Audio"):
            enhanced_audio_path = "enhanced_audio.wav"
            sf.write(enhanced_audio_path, reduced_noise, sample_rate)
            st.markdown(
                f'<a href="{enhanced_audio_path}" download="enhanced_audio.wav">Click here to download enhanced audio</a>',
                unsafe_allow_html=True,
            )

def audiorec_demo_app():

    # TITLE and Creator information
    st.title('streamlit audio recorder')
   

    # TUTORIAL: How to use STREAMLIT AUDIO RECORDER?
    # by calling this function an instance of the audio recorder is created
    # once a recording is completed, audio data will be saved to wav_audio_data

    wav_audio_data = st_audiorec() # tadaaaa! yes, that's it! :D

    # add some spacing and informative messages
    col_info, col_space = st.columns([0.57, 0.43])
    with col_info:
        st.write('\n')  # add vertical spacer
        st.write('\n')  # add vertical spacer
       

    if wav_audio_data is not None:
        # display audio data as received on the Python side
        col_playback, col_space = st.columns([0.58,0.42])
        with col_playback:
            st.audio(wav_audio_data, format='audio/wav')
model = "htdemucs"
extensions = ["mp3", "wav", "ogg", "flac"] 
two_stems = None 
mp3 = True
mp3_rate = 320
float32 = False 
int24 = False   
out_folder = 'output/htdemucs'
if not os.path.exists(out_folder):
    os.makedirs(out_folder)


def find_files(in_path):
    st.info(inp_path)
    out = []
    for file in Path(in_path).iterdir():
        if file.suffix.lower().lstrip(".") in extensions:
            out.append(file)
    return out



def copy_process_streams(process: sp.Popen):
    def raw(stream: Optional[IO[bytes]]) -> IO[bytes]:
        assert stream is not None
        if isinstance(stream, io.BufferedIOBase):
            stream = stream.raw
        return stream

    p_stdout, p_stderr = raw(process.stdout), raw(process.stderr)
    stream_by_fd: Dict[int, Tuple[IO[bytes], io.StringIO, IO[str]]] = {
        p_stdout.fileno(): (p_stdout, sys.stdout),
        p_stderr.fileno(): (p_stderr, sys.stderr),
    }
    fds = list(stream_by_fd.keys())

    while fds:
        ready, _, _ = select.select(fds, [], [])
        for fd in ready:
            p_stream, std = stream_by_fd[fd]
            raw_buf = p_stream.read(2 ** 16)
            if not raw_buf:
                fds.remove(fd)
                continue
            buf = raw_buf.decode()
            std.write(buf)
            std.flush()

def separate(inp=None, outp='output'):

    cmd = ["python", "-m", "demucs.separate", "-o", str(outp), "-n", model]
    if mp3:
        cmd += ["--mp3", f"--mp3-bitrate={mp3_rate}"]
    if float32:
        cmd += ["--float32"]
    if int24:
        cmd += ["--int24"]
    if two_stems is not None:
        cmd += [f"--two-stems={two_stems}"]
    files = [f'{f}' for f in find_files(inp)]
    if not files:
        st.info(f"No valid audio files in {inp}")
        return
    st.info("Going to separate the files")
   
    try:
        p = sp.Popen(cmd + files, stdout=sp.PIPE, stderr=sp.PIPE, shell=True, text=True)
        for line in p.stdout:
            # Display each line in the Streamlit app
            st.warning(line.strip())
        p.wait()
        # Optionally, display stderr as well
        for line in p.stderr:
            st.warning(line.strip())
        if p.returncode != 0:
            st.error("Command failed, something went wrong.")
        else:
            st.success("Command executed")
    except Exception as e:
        st.error(f"Error occured during working {e}")
def save(audio):
    folder = os.path.join('uploads', audio.name.split('.')[0].replace(' ','_').lower())
    if os.path.exists(folder):
        st.error(f"file already exists, taking '{folder}' as input ")
    else:    
        os.makedirs(folder)
        with open(os.path.join(folder, audio.name.replace(' ','').lower()), 'wb') as f:
            f.write(audio.getvalue())
        st.success("file uploaded")
    return folder

menu=["Log in","Sign Up"]
choice=st.sidebar.selectbox("Menu",menu)


if choice=="Log in":
    try:
         
        users=fetch_users()
        emails = []
        usernames = []
        passwords = []

        def forget_password():
            password1 = st.text_input(':blue[Password]', placeholder='Enter Your Password', type='password')
            password2 = st.text_input(':blue[Confirm Password]', placeholder='Confirm Your Password', type='password')


        for user in users:
            emails.append(user['key'])
            usernames.append(user['username'])
            passwords.append(user['password'])

        credentials = {'usernames': {}}
        for index in range(len(emails)):
            credentials['usernames'][usernames[index]] = {'name': emails[index], 'password': passwords[index]}

        Authenticator = stauth.Authenticate(credentials, cookie_name='Streamlit', key='abcdef', cookie_expiry_days=4)

        email, authentication_status, username = Authenticator.login(':green[Login]', 'main')

        info, info1 = st.columns(2)
        
        

        #if not authentication_status:
            #b=st.button("sign up")
            #sign()
            

        if username:
            if username in usernames:
                if authentication_status:
                    # let User see app
                    st.sidebar.subheader(f'Welcome {username}')
                    Authenticator.logout('Log Out', 'sidebar')
                    #Suppress the deprecated warning
     
                    col1,col2=st.columns(2)
                    with col1:
                        st.title(f'Hello  {username}')
                        
                        st.write("This free application will help you")
                        st.write("1-Seaprate drums, bass, and vocals from the rest of the accompaniment.Once you choose a song, it will separate the vocals from the instrumental ones. You will get four tracks: a karaoke version of your song (no vocals), acapella version (isolated vocals), drum and bass.")
                        st.write("2-record audio directly through the web app, saving the recordings for later use.")
                        st.write("3-In backgroung noice removal to enhance audio quality.")
                        st.write("4-In precise cutting of audio and music tracks")
                    with col2:
                    
                        lottie_url = "https://lottie.host/42e416e0-d4f3-41ae-9bf7-dee65309a74d/kyFC9yQFeI.json"
                        st.lottie(lottie_url, width=300, height=600)
                    st.write('<style>div.row-widget.stRadio>div{flex-direction:row;}</style>',unsafe_allow_html=True)
                    menu=["Seapration","Audio Splitter","Audio recording","Noise removal"]
                    choice=st.radio("Select",menu)
                    if choice=="Seapration":
                        st.subheader("Seprate")
                        audio=st.file_uploader("upload audio file",type=[])
                        st.audio(audio)
                        
                        if st.button("Seperate"):
                            with st.spinner("processing"):
                                inp_path = save(audio)
                                separate(inp_path)
                                st.balloons()
                                st.success("Task compeleted successfully")
                        st.header("Generated Files")
                        folders = os.listdir(out_folder)
                        selected = st.selectbox("select a music file", folders)
                        for file in os.listdir(os.path.join(out_folder, selected)):
                            st.subheader(file)
                            st.audio(f'{os.path.join(out_folder,selected,file)}')
                
                    elif choice=="Noise removal":
                        st.title("Audio Enhancement Tool")
                        noise()
                        
                           

                    elif choice=="Audio Splitter":
                        st.title("Audio Splitter")

                        # Upload an audio file
                        audio_file = st.file_uploader("Upload an audio file", type=["mp3", "wav", "gsm"])

                        if audio_file is not None:
                            # Create a directory for storing the split audio chunks
                            if not os.path.isdir("splitaudio"):
                                os.mkdir("splitaudio")

                            audio = AudioSegment.from_file(audio_file)
                            length_audio = len(audio)
                            st.write(f"Length of Audio File: {length_audio / 1000} seconds")

                            start_time_ms = st.slider("Select the start time (in seconds)", min_value=0, max_value=int(length_audio / 1000), step=1, value=0)
                            end_time_ms = st.slider("Select the end time (in seconds)", min_value=0, max_value=int(length_audio / 1000), step=1, value=int(length_audio / 1000))

                            start = start_time_ms * 1000  # Convert to milliseconds
                            end = end_time_ms * 1000  # Convert to milliseconds
                            counter = 0

                            if start >= end:
                                st.error("Start time must be less than end time.")
                            else:
                                selected_chunk = audio[start:end]
                                filename = f'splitaudio/selected_chunk.wav'
                                selected_chunk.export(filename, format="wav")

                                st.success("Selected portion extracted and saved.")
                                st.audio(filename, format="audio/wav")
                    elif choice=="Audio recording":
                        audiorec_demo_app()


                elif not authentication_status:
                    with info:
                        st.error('Incorrect Password or username')
                else:
                    with info:
                        st.warning('Please feed in your credentials')
            else:
                with info:
                    st.warning('Username does not exist, Please Sign up')
            
                    


    except:
        st.success('Refresh Page')
if choice=="Sign Up":
    sign_up()
