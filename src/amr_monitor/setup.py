from setuptools import find_packages, setup

package_name = 'amr_monitor'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(
        exclude=['test'],
    ),
    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name],
        ),
        (
            'share/' + package_name,
            ['package.xml'],
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='artur',
    maintainer_email='artur@example.com',
    description='Monitoring components for the MiniFactory AMR project',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
    'console_scripts': [
        'robot_status = amr_monitor.robot_status:main',
        'obstacle_monitor = amr_monitor.obstacle_monitor:main',
        'safety_supervisor = amr_monitor.safety_supervisor:main',
    ],
},
)
